# -*- coding: utf-8 -*-
"""R54-AHR Post-PNT closed material next boundary confirmation PCM-OP08 tests."""

from __future__ import annotations

from copy import deepcopy
from functools import lru_cache
from pathlib import Path
import sys

import pytest

TEST_DIR = Path(__file__).resolve().parent
if str(TEST_DIR) not in sys.path:
    sys.path.insert(0, str(TEST_DIR))

import emlis_ai_p7_r54_ahr_post_pnt_closed_material_next_boundary_confirmation_20260707 as pcm
from r54_ahr_post_pnt_pcm_compact_pnt_op08_fixture_20260708 import (
    compact_closed_pnt_op08_for_pcm_regression,
)


PCM_R6_FORBIDDEN_EXECUTION_KEYS = (
    "pnt_op08_default_builder_called_here",
    "pnt_op08_default_material_synthesized_here",
    "pnt_op08_builder_called_here",
    "pnt_op08_material_synthesized_here",
    "pnt_r11_decision_table_used_as_single_lane_here",
    "selected_post_nci_next_boundary_executed_here",
    "selected_handoff_or_stop_executed_here",
    "handoff_or_stop_envelope_executed_here",
    "selected_pcm_next_boundary_executed_here",
    "selected_pcm_next_boundary_execution_allowed_here",
    "execution_allowed_here",
    "post_pnt_closed_material_confirmation_result_memo_execution_allowed_here",
    "dhr_op05_called_here",
    "dhr_op05_builder_called_here",
    "dhr_op06_called_here",
    "dhr_op07_materialized_here",
    "dmd_execution_started_here",
    "r52_actual_execution_started_here",
    "actual_body_full_packet_generated_here",
    "actual_review_started_here",
    "actual_local_human_review_execution_started_here",
    "actual_operation_receipt_created_here",
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
    "p5_final_allowed",
    "p6_start_allowed",
    "p7_complete",
    "release_allowed",
    "full_backend_suite_green_confirmed",
    "rn_contract_green_confirmed",
    "rn_real_device_modal_verified_claimed_here",
)


PCM_R6_SIX_LANE_EXPECTED_LANE_REFS = (
    pcm.P7_R54_AHR_POST_PNT_PCM_LANE_DHR_OP05_MANUAL_HANDOFF_BOUNDARY_DESIGN_CANDIDATE_REF,
    pcm.P7_R54_AHR_POST_PNT_PCM_LANE_RETRY_OR_START_ACTUAL_LOCAL_ONLY_REVIEW_ROUTE_CANDIDATE_REF,
    pcm.P7_R54_AHR_POST_PNT_PCM_LANE_WAIT_EXTERNAL_BODYFREE_CLAIM_REINTAKE_CANDIDATE_REF,
    pcm.P7_R54_AHR_POST_PNT_PCM_LANE_REPAIR_RDB_CANDIDATE_OR_UPSTREAM_RESULT_CANDIDATE_REF,
    pcm.P7_R54_AHR_POST_PNT_PCM_LANE_MANUAL_HOLD_UNRESOLVED_POST_RDB08_CANDIDATE_REF,
    pcm.P7_R54_AHR_POST_PNT_PCM_LANE_BLOCKED_BODYFREE_LEAK_PROMOTION_OR_AUTORUN_CANDIDATE_REF,
)


PCM_R6_EXPECTED_NEXT_WORK_CLASS_REFS = (
    pcm.P7_R54_AHR_POST_PNT_PCM_NEXT_WORK_CLASS_NEXT_DESIGN_CANDIDATE_REF,
    pcm.P7_R54_AHR_POST_PNT_PCM_NEXT_WORK_CLASS_NEXT_DESIGN_CANDIDATE_REF,
    pcm.P7_R54_AHR_POST_PNT_PCM_NEXT_WORK_CLASS_WAIT_HOLD_REF,
    pcm.P7_R54_AHR_POST_PNT_PCM_NEXT_WORK_CLASS_NEXT_DESIGN_CANDIDATE_REF,
    pcm.P7_R54_AHR_POST_PNT_PCM_NEXT_WORK_CLASS_STOP_REF,
    pcm.P7_R54_AHR_POST_PNT_PCM_NEXT_WORK_CLASS_STOP_REF,
)


@lru_cache(maxsize=6)
def _cached_closed_pnt_op08(index: int = 0) -> tuple[tuple[str, object], ...]:
    return tuple(compact_closed_pnt_op08_for_pcm_regression(index).items())


def _closed_pnt_op08(index: int = 0) -> dict[str, object]:
    return dict(_cached_closed_pnt_op08(index))


@lru_cache(maxsize=6)
def _cached_pcm_op07_from_closed(index: int = 0) -> tuple[tuple[str, object], ...]:
    op01 = pcm.build_p7_r54_ahr_post_pnt_pcm_op01_explicit_closed_pnt_op08_material_intake(
        pnt_op08_bodyfree_result_memo_closure_material=_closed_pnt_op08(index),
    )
    op02 = pcm.build_p7_r54_ahr_post_pnt_pcm_op02_closed_material_contract_validation(op01)
    op03 = pcm.build_p7_r54_ahr_post_pnt_pcm_op03_single_selected_lane_confirmation(op02)
    op04 = pcm.build_p7_r54_ahr_post_pnt_pcm_op04_next_work_class_resolver(op03)
    op05 = pcm.build_p7_r54_ahr_post_pnt_pcm_op05_next_design_candidate_envelope_materialization(op04)
    op06 = pcm.build_p7_r54_ahr_post_pnt_pcm_op06_bodyfree_no_touch_no_promotion_no_auto_execution_guard(op05)
    op07 = pcm.build_p7_r54_ahr_post_pnt_pcm_op07_validation_plan_result_memo_draft_material(op06)
    return tuple(op07.items())


def _pcm_op07_from_closed(index: int = 0) -> dict[str, object]:
    return deepcopy(dict(_cached_pcm_op07_from_closed(index)))


def _pcm_op08_from_closed(index: int = 0) -> dict[str, object]:
    return pcm.build_p7_r54_ahr_post_pnt_pcm_op08_bodyfree_post_pnt_closed_material_next_boundary_confirmation_closure(_pcm_op07_from_closed(index))


def _assert_pcm_r6_no_execution_or_claim(material: dict[str, object]) -> None:
    for key in PCM_R6_FORBIDDEN_EXECUTION_KEYS:
        if key in material:
            assert material[key] is False, key
    assert material["git_connection_required"] is False
    assert material["git_checked"] is False
    assert material["body_free"] is True
    assert material["pnt_op08_builder_not_called"] is True
    assert material["pnt_op08_material_not_synthesized"] is True
    assert material["dhr_op05_not_called"] is True
    assert material["dhr_op06_not_called"] is True
    assert material["dmd_r52_not_executed"] is True
    assert material["actual_review_not_started"] is True
    assert material["p5_p6_p8_p7_release_not_started"] is True
    assert material["p8_question_design_not_started"] is True
    assert material["p8_question_implementation_not_started"] is True
    assert material["api_db_rn_runtime_response_key_not_changed"] is True
    assert material["dhr_op05_call_allowed_here"] is False
    assert material["dhr_op05_builder_call_allowed_here"] is False
    assert material["actual_review_start_allowed_here"] is False
    assert material["repair_execution_allowed_here"] is False
    assert material["raw_evidence_request_allowed_here"] is False
    assert material["p8_question_design_allowed_here"] is False
    assert material["api_db_rn_response_key_change_allowed_here"] is False
    assert material["json_schema_file_creation_allowed_here"] is False
    assert material["full_backend_suite_green_confirmed"] is False
    assert material["rn_contract_green_confirmed"] is False
    assert material["rn_real_device_modal_verified_claimed_here"] is False


@pytest.mark.parametrize(
    ("case_index", "expected_lane", "expected_next_work_class"),
    [
        (index, lane, next_work_class)
        for index, (lane, next_work_class) in enumerate(zip(PCM_R6_SIX_LANE_EXPECTED_LANE_REFS, PCM_R6_EXPECTED_NEXT_WORK_CLASS_REFS))
    ],
    ids=["dhr", "retry", "wait", "repair", "unresolved", "blocked"],
)
def test_pcm_op08_closes_all_six_valid_outcomes_as_next_design_candidate_wait_or_stop_without_execution(
    case_index: int,
    expected_lane: str,
    expected_next_work_class: str,
) -> None:
    op08 = _pcm_op08_from_closed(case_index)

    assert pcm.assert_p7_r54_ahr_post_pnt_pcm_op08_bodyfree_post_pnt_closed_material_next_boundary_confirmation_closure_contract(op08) is True
    assert set(op08) == set(pcm.P7_R54_AHR_POST_PNT_PCM_OP08_REQUIRED_FIELD_REFS)
    assert op08["pcm_op08_status_ref"] == pcm.P7_R54_AHR_POST_PNT_PCM_OP08_STATUS_CLOSED_STOPPED_REF
    assert op08["pcm_op08_closed_stopped"] is True
    assert op08["post_pnt_closed_material_confirmation_result_memo_closed_here"] is True
    assert op08["op07_ready_for_op08"] is True
    assert op08["selected_pnt_lane_ref"] == expected_lane
    assert op08["selected_pcm_next_work_class_ref"] == expected_next_work_class
    assert op08["selected_pcm_next_boundary_ref"] == pcm.P7_R54_AHR_POST_PNT_PCM_LANE_TO_SELECTED_PCM_NEXT_BOUNDARY_REF_MAP[expected_lane]
    assert op08["selected_pcm_next_boundary_kind_ref"] == pcm.P7_R54_AHR_POST_PNT_PCM_LANE_TO_SELECTED_PCM_NEXT_BOUNDARY_KIND_REF_MAP[expected_lane]
    assert op08["selected_post_nci_next_boundary_not_executed"] is True
    assert op08["selected_handoff_or_stop_not_executed"] is True
    assert op08["selected_pcm_next_boundary_not_executed"] is True
    assert op08["selected_pcm_next_boundary_envelope_materialized_here"] is True
    assert op08["validation_result_status_refs_recorded"] is True
    assert op08["pcm_op08_blocker_refs"] == []
    assert op08["not_yet_implemented_steps"] == []
    assert tuple(op08["implemented_steps"]) == pcm.P7_R54_AHR_POST_PNT_PCM_OP08_IMPLEMENTED_STEPS
    _assert_pcm_r6_no_execution_or_claim(op08)

    if expected_next_work_class == pcm.P7_R54_AHR_POST_PNT_PCM_NEXT_WORK_CLASS_NEXT_DESIGN_CANDIDATE_REF:
        assert op08["next_required_step"] == pcm.P7_R54_AHR_POST_PNT_PCM_NEXT_STEP_STOP_AFTER_OP08_NEXT_DESIGN_CANDIDATE_REF
        assert op08["next_design_document_allowed"] is True
        assert op08["next_design_document_candidate_ref"] == pcm.P7_R54_AHR_POST_PNT_PCM_LANE_TO_NEXT_DESIGN_OR_HOLD_STOP_REFS[expected_lane]
        assert op08["manual_wait_required"] is False
        assert op08["manual_stop_required"] is False
    elif expected_next_work_class == pcm.P7_R54_AHR_POST_PNT_PCM_NEXT_WORK_CLASS_WAIT_HOLD_REF:
        assert op08["next_required_step"] == pcm.P7_R54_AHR_POST_PNT_PCM_NEXT_STEP_WAIT_HOLD_AFTER_OP08_REF
        assert op08["next_design_document_allowed"] is False
        assert op08["manual_wait_required"] is True
        assert op08["manual_stop_required"] is False
    else:
        assert op08["next_required_step"] == pcm.P7_R54_AHR_POST_PNT_PCM_NEXT_STEP_STOP_AFTER_OP08_REF
        assert op08["next_design_document_allowed"] is False
        assert op08["manual_wait_required"] is False
        assert op08["manual_stop_required"] is True


@pytest.mark.parametrize(
    ("case_index", "expected_lane", "expected_next_work_class"),
    [
        (index, lane, next_work_class)
        for index, (lane, next_work_class) in enumerate(zip(PCM_R6_SIX_LANE_EXPECTED_LANE_REFS, PCM_R6_EXPECTED_NEXT_WORK_CLASS_REFS))
    ],
    ids=["dhr", "retry", "wait", "repair", "unresolved", "blocked"],
)
def test_pcm_op08_records_selected_pcm_boundary_but_never_promotes_to_downstream_execution(
    case_index: int,
    expected_lane: str,
    expected_next_work_class: str,
) -> None:
    op08 = _pcm_op08_from_closed(case_index)

    assert op08["selected_pnt_lane_ref"] == expected_lane
    assert op08["selected_pcm_next_work_class_ref"] == expected_next_work_class
    assert op08["selected_pcm_next_boundary_ref"] != "missing"
    assert op08["selected_pcm_next_boundary_not_executed"] is True
    assert op08["selected_pcm_next_boundary_execution_allowed_here"] is False
    assert op08["pcm_op08_records_next_design_candidate_hold_or_stop_only"] is True
    assert op08["pcm_op08_does_not_execute_selected_post_nci_next_boundary"] is True
    assert op08["pcm_op08_does_not_execute_selected_pcm_next_boundary"] is True
    assert op08["pcm_op08_does_not_call_dhr_op05"] is True
    assert op08["pcm_op08_does_not_materialize_p8_question_spec"] is True
    _assert_pcm_r6_no_execution_or_claim(op08)


def test_pcm_op08_waits_when_explicit_op07_closed_material_is_missing_without_synthesizing_pnt_material() -> None:
    op08 = pcm.build_p7_r54_ahr_post_pnt_pcm_op08_bodyfree_post_pnt_closed_material_next_boundary_confirmation_closure()

    assert pcm.assert_p7_r54_ahr_post_pnt_pcm_op08_bodyfree_post_pnt_closed_material_next_boundary_confirmation_closure_contract(op08) is True
    assert op08["pcm_op08_status_ref"] == pcm.P7_R54_AHR_POST_PNT_PCM_OP08_STATUS_WAITING_FOR_EXPLICIT_PNT_OP08_CLOSED_MATERIAL_REF
    assert op08["pcm_op08_waiting_for_explicit_pnt_op08_closed_material"] is True
    assert op08["post_pnt_closed_material_confirmation_result_memo_closed_here"] is False
    assert op08["op07_material_present"] is False
    assert op08["next_required_step"] == pcm.P7_R54_AHR_POST_PNT_PCM_NEXT_STEP_WAIT_FOR_EXPLICIT_PNT_OP08_CLOSED_MATERIAL_REF
    assert "explicit_pnt_op08_closed_material_required" in op08["pcm_op08_blocker_refs"]
    _assert_pcm_r6_no_execution_or_claim(op08)


def test_pcm_op08_repairs_ambiguous_multi_lane_material_instead_of_treating_decision_table_as_current_lane() -> None:
    op01 = pcm.build_p7_r54_ahr_post_pnt_pcm_op01_explicit_closed_pnt_op08_material_intake(
        pnt_op08_bodyfree_result_memo_closure_material=_closed_pnt_op08(0),
    )
    op02 = pcm.build_p7_r54_ahr_post_pnt_pcm_op02_closed_material_contract_validation(op01)
    ambiguous_op02 = deepcopy(op02)
    ambiguous_op02["decision_table"] = [{"lane_ref": PCM_R6_SIX_LANE_EXPECTED_LANE_REFS[0]}]
    op03 = pcm.build_p7_r54_ahr_post_pnt_pcm_op03_single_selected_lane_confirmation(ambiguous_op02)
    op04 = pcm.build_p7_r54_ahr_post_pnt_pcm_op04_next_work_class_resolver(op03)
    op05 = pcm.build_p7_r54_ahr_post_pnt_pcm_op05_next_design_candidate_envelope_materialization(op04)
    op06 = pcm.build_p7_r54_ahr_post_pnt_pcm_op06_bodyfree_no_touch_no_promotion_no_auto_execution_guard(op05)
    op07 = pcm.build_p7_r54_ahr_post_pnt_pcm_op07_validation_plan_result_memo_draft_material(op06)
    op08 = pcm.build_p7_r54_ahr_post_pnt_pcm_op08_bodyfree_post_pnt_closed_material_next_boundary_confirmation_closure(op07)

    assert op03["pcm_op03_status_ref"] == pcm.P7_R54_AHR_POST_PNT_PCM_OP03_STATUS_REPAIR_REQUIRED_FOR_MULTI_OR_AMBIGUOUS_LANE_REF
    assert pcm.assert_p7_r54_ahr_post_pnt_pcm_op08_bodyfree_post_pnt_closed_material_next_boundary_confirmation_closure_contract(op08) is True
    assert op08["pcm_op08_status_ref"] == pcm.P7_R54_AHR_POST_PNT_PCM_OP08_STATUS_REPAIR_REQUIRED_FOR_POST_PNT_CONFIRMATION_INPUTS_REF
    assert op08["pcm_op08_repair_required_for_post_pnt_confirmation_inputs"] is True
    assert "pcm_op07_result_memo_draft_repair_required_before_op08_closure" in op08["pcm_op08_blocker_refs"]
    assert op08["next_required_step"] == pcm.P7_R54_AHR_POST_PNT_PCM_NEXT_STEP_REPAIR_OP08_CLOSURE_INPUTS_REF
    assert op08["post_pnt_closed_material_confirmation_result_memo_closed_here"] is False
    _assert_pcm_r6_no_execution_or_claim(op08)


@pytest.mark.parametrize(
    ("mutation_key", "mutation_value", "expected_blocker"),
    [
        ("question_text", "do not materialize", "op08_closure_forbidden_payload_key_detected"),
        ("raw_evidence", "raw", "op08_closure_forbidden_payload_key_detected"),
        ("stdout", "not allowed", "op08_closure_forbidden_payload_key_detected"),
        ("dhr_op05_called_here", True, "op08_closure_promotion_or_autorun_claim_detected"),
        ("p8_question_design_started", True, "op08_closure_promotion_or_autorun_claim_detected"),
        ("release_allowed", True, "op08_closure_promotion_or_autorun_claim_detected"),
        ("full_backend_suite_green_confirmed", True, "op08_closure_promotion_or_autorun_claim_detected"),
        ("api_changed", True, "op08_closure_api_db_rn_runtime_response_key_or_p8_question_touch_detected"),
        ("response_key_changed", True, "op08_closure_api_db_rn_runtime_response_key_or_p8_question_touch_detected"),
    ],
)
def test_pcm_op08_blocks_body_payload_promotion_public_contract_and_green_claim_mutations(
    mutation_key: str,
    mutation_value: object,
    expected_blocker: str,
) -> None:
    op07 = _pcm_op07_from_closed(0)
    op07[mutation_key] = mutation_value

    op08 = pcm.build_p7_r54_ahr_post_pnt_pcm_op08_bodyfree_post_pnt_closed_material_next_boundary_confirmation_closure(op07)

    assert pcm.assert_p7_r54_ahr_post_pnt_pcm_op08_bodyfree_post_pnt_closed_material_next_boundary_confirmation_closure_contract(op08) is True
    assert op08["pcm_op08_status_ref"] == pcm.P7_R54_AHR_POST_PNT_PCM_OP08_STATUS_BLOCKED_BODYFREE_LEAK_PROMOTION_OR_AUTORUN_REF
    assert op08["pcm_op08_bodyfree_leak_promotion_or_autorun_blocked"] is True
    assert expected_blocker in op08["pcm_op08_blocker_refs"]
    assert op08["next_required_step"] == pcm.P7_R54_AHR_POST_PNT_PCM_NEXT_STEP_BLOCKED_OP08_CLOSURE_REF
    assert op08["post_pnt_closed_material_confirmation_result_memo_closed_here"] is False
    _assert_pcm_r6_no_execution_or_claim(op08)


@pytest.mark.parametrize(
    ("mutation_key", "mutation_value"),
    [
        ("selected_pcm_next_boundary_execution_allowed_here", True),
        ("execution_allowed_here", True),
        ("post_pnt_closed_material_confirmation_result_memo_execution_allowed_here", True),
        ("dhr_op05_call_allowed_here", True),
        ("p8_question_design_allowed_here", True),
        ("release_allowed", True),
        ("full_backend_suite_green_confirmed", True),
        ("rn_contract_green_confirmed", True),
        ("rn_real_device_modal_verified_claimed_here", True),
        ("pnt_op08_builder_not_called", False),
        ("pnt_op08_material_not_synthesized", False),
        ("dhr_op05_not_called", False),
        ("p8_question_design_not_started", False),
        ("api_db_rn_runtime_response_key_not_changed", False),
    ],
)
def test_pcm_op08_contract_rejects_downstream_execution_and_release_claim_mutation(
    mutation_key: str,
    mutation_value: object,
) -> None:
    op08 = _pcm_op08_from_closed(0)
    op08[mutation_key] = mutation_value

    with pytest.raises(ValueError):
        pcm.assert_p7_r54_ahr_post_pnt_pcm_op08_bodyfree_post_pnt_closed_material_next_boundary_confirmation_closure_contract(op08)


def test_pcm_op08_full_title_aliases_match_short_builder_and_contract() -> None:
    op07 = _pcm_op07_from_closed(0)
    short_op08 = pcm.build_p7_r54_ahr_post_pnt_pcm_op08_bodyfree_post_pnt_closed_material_next_boundary_confirmation_closure(op07)
    long_op08 = pcm.build_p7_r54_ahr_post_pnt_closed_material_next_boundary_confirmation_pcm_op08_bodyfree_closure(op07)

    assert short_op08 == long_op08
    assert pcm.assert_p7_r54_ahr_post_pnt_closed_material_next_boundary_confirmation_pcm_op08_bodyfree_closure_contract(long_op08) is True
