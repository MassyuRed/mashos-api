# -*- coding: utf-8 -*-
"""R54-AHR Post-NCI selected handoff-or-stop decision triage PNT-OP02/OP03 tests."""

from __future__ import annotations

from copy import deepcopy
from pathlib import Path
import sys

import pytest

TEST_DIR = Path(__file__).resolve().parent
if str(TEST_DIR) not in sys.path:
    sys.path.insert(0, str(TEST_DIR))

import emlis_ai_p7_r54_ahr_post_nci_selected_handoff_or_stop_decision_triage_20260707 as pnt
import emlis_ai_p7_r54_ahr_post_rdb08_selected_next_stage_candidate_intake_20260706 as nci
import emlis_ai_p7_r54_ahr_post_mrb08_dhr_op04_result_manual_decision_20260705 as rdb
from test_r54_ahr_post_dri_dhr_op04_manual_reintake_mrb_op06_op07_20260705 import (
    _op05_confirmed,
    _op05_invalid_result,
    _op05_not_confirmed,
    _op05_waiting_result,
)
from test_r54_ahr_post_rdb08_selected_next_stage_candidate_intake_nci_op08_result_20260706 import (
    _chain_from_op03,
    _chain_from_op05,
    _closed_from_chain,
    _op03_with_selected_candidate_shape,
    _result_memo,
    _validation_summary,
)


PNT_R3_FORBIDDEN_EXECUTION_KEYS = (
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
)


def _valid_closed_nci_op08_from_chain(chain: tuple[dict[str, object], dict[str, object], dict[str, object], dict[str, object]]) -> dict[str, object]:
    return _closed_from_chain(
        chain,
        validation_summary=_validation_summary(),
        result_memo=_result_memo(),
    )


def _pnt_op01_from_nci_op08(nci_op08: dict[str, object]) -> dict[str, object]:
    return pnt.build_p7_r54_ahr_post_nci_pnt_op01_explicit_nci_op08_bodyfree_result_memo_closure_intake(
        nci_op08_bodyfree_selected_candidate_intake_result_memo_closure=nci_op08,
    )


def _pnt_op02_from_nci_op08(nci_op08: dict[str, object]) -> dict[str, object]:
    return pnt.build_p7_r54_ahr_post_nci_pnt_op02_selected_handoff_or_stop_shape_validation(
        _pnt_op01_from_nci_op08(nci_op08),
    )


def _valid_hand_off_nci_op08(op05: dict[str, object]) -> dict[str, object]:
    return _valid_closed_nci_op08_from_chain(_chain_from_op05(op05))


def _unresolved_stop_nci_op08() -> dict[str, object]:
    unresolved_op03 = _op03_with_selected_candidate_shape(
        rdb_status_ref=rdb.P7_R54_AHR_POST_MRB08_RDB_STATUS_INCOMPLETE_UNRESOLVED_MANUAL_HOLD_STOPPED_REF,
        candidate_ref=rdb.P7_R54_AHR_POST_MRB08_RDB_NEXT_STEP_MANUAL_HOLD_UNRESOLVED_REF,
        candidate_kind_ref=rdb.P7_R54_AHR_POST_MRB08_RDB_CANDIDATE_KIND_UNRESOLVED_REF,
        decision_lane_ref=rdb.P7_R54_AHR_POST_MRB08_RDB_DECISION_LANE_MANUAL_HOLD_UNRESOLVED_REF,
    )
    return _valid_closed_nci_op08_from_chain(_chain_from_op03(unresolved_op03))


def _blocked_stop_nci_op08() -> dict[str, object]:
    blocked_op03 = _op03_with_selected_candidate_shape(
        rdb_status_ref=rdb.P7_R54_AHR_POST_MRB08_RDB_STATUS_BLOCKED_BODYFREE_LEAK_PROMOTION_OR_AUTORUN_REF,
        candidate_ref=rdb.P7_R54_AHR_POST_MRB08_RDB_NEXT_STEP_BLOCKED_POST_MRB08_REF,
        candidate_kind_ref=rdb.P7_R54_AHR_POST_MRB08_RDB_CANDIDATE_KIND_BLOCKED_REF,
        decision_lane_ref=rdb.P7_R54_AHR_POST_MRB08_RDB_DECISION_LANE_BLOCKED_REF,
    )
    return _valid_closed_nci_op08_from_chain(_chain_from_op03(blocked_op03))


def _six_lane_cases() -> tuple[tuple[dict[str, object], str, str, str, str, str], ...]:
    return (
        (
            _valid_hand_off_nci_op08(_op05_confirmed()),
            pnt.P7_R54_AHR_POST_NCI_PNT_LANE_DHR_OP05_BOUNDARY_DESIGN_CANDIDATE_REF,
            pnt.P7_R54_AHR_POST_NCI_PNT_SELECTED_HANDOFF_DHR_OP05_BOUNDARY_REF,
            pnt.P7_R54_AHR_POST_NCI_PNT_HANDOFF_ENVELOPE_KIND_REF,
            pnt.P7_R54_AHR_POST_NCI_PNT_STATUS_DHR_OP05_BOUNDARY_DESIGN_CANDIDATE_STOPPED_REF,
            "dhr_op05_manual_handoff_boundary_design_candidate_present",
        ),
        (
            _valid_hand_off_nci_op08(_op05_not_confirmed()),
            pnt.P7_R54_AHR_POST_NCI_PNT_LANE_RETRY_START_ROUTE_CANDIDATE_REF,
            pnt.P7_R54_AHR_POST_NCI_PNT_SELECTED_HANDOFF_RETRY_START_REF,
            pnt.P7_R54_AHR_POST_NCI_PNT_HANDOFF_ENVELOPE_KIND_REF,
            pnt.P7_R54_AHR_POST_NCI_PNT_STATUS_RETRY_START_ROUTE_BOUNDARY_CANDIDATE_STOPPED_REF,
            "retry_start_route_boundary_candidate_present",
        ),
        (
            _valid_hand_off_nci_op08(_op05_waiting_result()),
            pnt.P7_R54_AHR_POST_NCI_PNT_LANE_WAIT_EXTERNAL_BODYFREE_CLAIM_REF,
            pnt.P7_R54_AHR_POST_NCI_PNT_SELECTED_HANDOFF_WAIT_EXTERNAL_CLAIM_REF,
            pnt.P7_R54_AHR_POST_NCI_PNT_HANDOFF_ENVELOPE_KIND_REF,
            pnt.P7_R54_AHR_POST_NCI_PNT_STATUS_WAIT_EXTERNAL_BODYFREE_CLAIM_HOLD_STOPPED_REF,
            "wait_external_bodyfree_claim_hold_present",
        ),
        (
            _valid_hand_off_nci_op08(_op05_invalid_result()),
            pnt.P7_R54_AHR_POST_NCI_PNT_LANE_REPAIR_BOUNDARY_CANDIDATE_REF,
            pnt.P7_R54_AHR_POST_NCI_PNT_SELECTED_HANDOFF_REPAIR_BOUNDARY_REF,
            pnt.P7_R54_AHR_POST_NCI_PNT_HANDOFF_ENVELOPE_KIND_REF,
            pnt.P7_R54_AHR_POST_NCI_PNT_STATUS_REPAIR_BOUNDARY_CANDIDATE_STOPPED_REF,
            "repair_boundary_candidate_present",
        ),
        (
            _unresolved_stop_nci_op08(),
            pnt.P7_R54_AHR_POST_NCI_PNT_LANE_MANUAL_HOLD_UNRESOLVED_REF,
            pnt.P7_R54_AHR_POST_NCI_PNT_SELECTED_STOP_MANUAL_HOLD_REF,
            pnt.P7_R54_AHR_POST_NCI_PNT_STOP_ENVELOPE_KIND_REF,
            pnt.P7_R54_AHR_POST_NCI_PNT_STATUS_MANUAL_HOLD_UNRESOLVED_STOPPED_REF,
            "manual_hold_unresolved_stop_present",
        ),
        (
            _blocked_stop_nci_op08(),
            pnt.P7_R54_AHR_POST_NCI_PNT_LANE_BLOCKED_BODYFREE_PROMOTION_AUTORUN_REF,
            pnt.P7_R54_AHR_POST_NCI_PNT_SELECTED_STOP_BLOCKED_REF,
            pnt.P7_R54_AHR_POST_NCI_PNT_STOP_ENVELOPE_KIND_REF,
            pnt.P7_R54_AHR_POST_NCI_PNT_STATUS_BLOCKED_BODYFREE_PROMOTION_AUTORUN_STOPPED_REF,
            "blocked_bodyfree_promotion_autorun_stop_present",
        ),
    )


def _assert_r3_no_downstream_execution(material: dict[str, object]) -> None:
    for key in PNT_R3_FORBIDDEN_EXECUTION_KEYS:
        assert material[key] is False, key
    assert material["git_connection_required"] is False
    assert material["git_checked"] is False
    assert material["body_free"] is True


@pytest.mark.parametrize(
    ("nci_op08", "expected_lane", "expected_ref", "expected_kind", "_expected_status", "_expected_flag"),
    _six_lane_cases(),
)
def test_pnt_op02_validates_all_six_selected_handoff_or_stop_shapes_without_lane_resolution(
    nci_op08: dict[str, object],
    expected_lane: str,
    expected_ref: str,
    expected_kind: str,
    _expected_status: str,
    _expected_flag: str,
) -> None:
    op02 = _pnt_op02_from_nci_op08(nci_op08)

    assert pnt.assert_p7_r54_ahr_post_nci_selected_handoff_or_stop_decision_triage_pnt_op02_selected_handoff_or_stop_shape_validation_contract(op02) is True
    assert op02["pnt_op02_status_ref"] == pnt.P7_R54_AHR_POST_NCI_PNT_OP02_STATUS_SHAPE_VALID_STOPPED_REF
    assert op02["selected_nci_lane_ref"] == expected_lane
    assert op02["selected_handoff_or_stop_ref"] == expected_ref
    assert op02["selected_handoff_or_stop_kind_ref"] == expected_kind
    assert op02["expected_selected_handoff_or_stop_ref"] == expected_ref
    assert op02["expected_selected_handoff_or_stop_kind_ref"] == expected_kind
    assert op02["selected_handoff_or_stop_shape_valid"] is True
    assert op02["selected_handoff_or_stop_ref_matches_lane"] is True
    assert op02["selected_handoff_or_stop_kind_matches_lane"] is True
    assert op02["handoff_or_stop_envelope_kind_consistent"] is True
    assert op02["handoff_or_stop_envelope_presence_consistent"] is True
    assert op02["pnt_op02_does_not_resolve_selected_handoff_or_stop_lane"] is True
    assert op02["pnt_op02_does_not_materialize_next_boundary_selection"] is True
    assert op02["next_required_step"] == pnt.P7_R54_AHR_POST_NCI_PNT_OP03_STEP_REF
    assert op02["pnt_op02_blocker_refs"] == []
    _assert_r3_no_downstream_execution(op02)


@pytest.mark.parametrize(
    ("nci_op08", "expected_lane", "expected_ref", "expected_kind", "expected_status", "expected_flag"),
    _six_lane_cases(),
)
def test_pnt_op03_resolves_all_six_lanes_but_does_not_materialize_op04_or_execute_downstream(
    nci_op08: dict[str, object],
    expected_lane: str,
    expected_ref: str,
    expected_kind: str,
    expected_status: str,
    expected_flag: str,
) -> None:
    op02 = _pnt_op02_from_nci_op08(nci_op08)
    op03 = pnt.build_p7_r54_ahr_post_nci_pnt_op03_selected_handoff_or_stop_lane_consistency_resolver(op02)

    assert pnt.assert_p7_r54_ahr_post_nci_selected_handoff_or_stop_decision_triage_pnt_op03_selected_handoff_or_stop_lane_consistency_resolver_contract(op03) is True
    assert op03["pnt_op03_status_ref"] == expected_status
    assert op03["selected_pnt_status_ref"] == expected_status
    assert op03["selected_pnt_lane_ref"] == expected_lane
    assert op03["selected_pnt_lane_resolved"] is True
    assert op03["selected_handoff_or_stop_ref"] == expected_ref
    assert op03["selected_handoff_or_stop_kind_ref"] == expected_kind
    assert op03["selected_handoff_or_stop_not_executed"] is True
    assert op03["selected_post_nci_next_boundary_candidate_ref"] == expected_ref
    assert op03["selected_post_nci_next_boundary_candidate_kind_ref"] == pnt.P7_R54_AHR_POST_NCI_PNT_LANE_TO_NEXT_DESIGN_OR_STOP_KIND_REF_MAP[expected_lane]
    assert op03["selected_post_nci_next_boundary_not_executed"] is True
    assert op03["selected_post_nci_next_boundary_execution_allowed_here"] is False
    assert op03["selected_post_nci_next_boundary_materialized_here"] is False
    assert op03[expected_flag] is True
    assert sum(op03[key] is True for key in pnt.P7_R54_AHR_POST_NCI_PNT_OP03_LANE_FLAG_REFS) == 1
    assert op03["pnt_op03_blocker_refs"] == []
    assert op03["next_required_step"] == pnt.P7_R54_AHR_POST_NCI_PNT_OP04_STEP_REF
    _assert_r3_no_downstream_execution(op03)


def test_pnt_op02_repairs_when_selected_handoff_or_stop_ref_is_missing() -> None:
    nci_op08 = _valid_hand_off_nci_op08(_op05_confirmed())
    op01 = _pnt_op01_from_nci_op08(nci_op08)
    mutated = deepcopy(op01)
    mutated["selected_handoff_or_stop_ref"] = ""

    op02 = pnt.build_p7_r54_ahr_post_nci_pnt_op02_selected_handoff_or_stop_shape_validation(mutated)

    assert pnt.assert_p7_r54_ahr_post_nci_selected_handoff_or_stop_decision_triage_pnt_op02_selected_handoff_or_stop_shape_validation_contract(op02) is True
    assert op02["pnt_op02_status_ref"] == pnt.P7_R54_AHR_POST_NCI_PNT_OP02_STATUS_REPAIR_REQUIRED_REF
    assert "selected_handoff_or_stop_ref_missing" in op02["pnt_op02_blocker_refs"]
    assert op02["next_required_step"] == pnt.P7_R54_AHR_POST_NCI_PNT_NEXT_STEP_REPAIR_SELECTED_HANDOFF_OR_STOP_SHAPE_REF
    _assert_r3_no_downstream_execution(op02)


@pytest.mark.parametrize(
    ("mutation_key", "mutation_value", "expected_blocker"),
    [
        ("selected_handoff_or_stop_ref", "unknown_selected_ref", "selected_handoff_or_stop_ref_unknown_or_not_allowed"),
        ("selected_handoff_or_stop_kind_ref", "unknown_kind", "selected_handoff_or_stop_kind_ref_unknown_or_not_allowed"),
        ("selected_next_design_or_stop_ref", pnt.P7_R54_AHR_POST_NCI_PNT_SELECTED_HANDOFF_RETRY_START_REF, "selected_handoff_or_stop_ref_and_selected_next_design_or_stop_ref_mismatch"),
        ("selected_next_design_or_stop_kind_ref", nci.P7_R54_AHR_POST_RDB08_NCI_NEXT_STOP_KIND_BLOCKED_REF, "selected_next_design_or_stop_kind_ref_does_not_match_selected_nci_lane"),
        ("op07_handoff_or_stop_envelope_kind_ref", pnt.P7_R54_AHR_POST_NCI_PNT_STOP_ENVELOPE_KIND_REF, "op07_handoff_or_stop_envelope_kind_ref_mismatch"),
        ("op07_handoff_envelope_present", False, "op07_handoff_or_stop_envelope_presence_mismatch"),
    ],
)
def test_pnt_op02_repairs_ref_kind_and_envelope_mismatches_without_promotion(
    mutation_key: str,
    mutation_value: object,
    expected_blocker: str,
) -> None:
    nci_op08 = _valid_hand_off_nci_op08(_op05_confirmed())
    op01 = _pnt_op01_from_nci_op08(nci_op08)
    mutated = deepcopy(op01)
    mutated[mutation_key] = mutation_value

    op02 = pnt.build_p7_r54_ahr_post_nci_pnt_op02_selected_handoff_or_stop_shape_validation(mutated)

    assert pnt.assert_p7_r54_ahr_post_nci_selected_handoff_or_stop_decision_triage_pnt_op02_selected_handoff_or_stop_shape_validation_contract(op02) is True
    assert op02["pnt_op02_status_ref"] == pnt.P7_R54_AHR_POST_NCI_PNT_OP02_STATUS_REPAIR_REQUIRED_REF
    assert expected_blocker in op02["pnt_op02_blocker_refs"]
    assert op02["selected_handoff_or_stop_shape_valid"] is False
    assert op02["next_required_step"] == pnt.P7_R54_AHR_POST_NCI_PNT_NEXT_STEP_REPAIR_SELECTED_HANDOFF_OR_STOP_SHAPE_REF
    _assert_r3_no_downstream_execution(op02)


@pytest.mark.parametrize(
    ("mutation_key", "mutation_value", "expected_blocker"),
    [
        ("selected_handoff_or_stop_not_executed", False, "selected_handoff_or_stop_not_executed_false"),
        ("selected_next_design_or_stop_not_executed", False, "selected_next_design_or_stop_not_executed_false"),
        ("rdb08_selected_next_stage_candidate_not_executed", False, "rdb08_selected_next_stage_candidate_not_executed_false"),
        ("op07_handoff_or_stop_envelope_bodyfree", False, "op07_handoff_or_stop_envelope_not_bodyfree"),
        ("question_text", "blocked_question", "op02_input_forbidden_payload_key_detected"),
        ("raw_evidence", "blocked_raw_evidence", "op02_input_forbidden_payload_key_detected"),
        ("local_path", "/tmp/not_allowed", "op02_input_forbidden_payload_key_detected"),
        ("hash", "blocked_hash", "op02_input_forbidden_payload_key_detected"),
        ("stdout", "terminal body leak", "op02_input_body_like_value_detected"),
        ("dhr_op05_called_here", True, "op02_input_promotion_or_autorun_claim_detected"),
        ("api_changed", True, "op02_input_api_db_rn_runtime_response_key_or_p8_question_touch_detected"),
    ],
)
def test_pnt_op02_blocks_not_executed_false_body_leak_promotion_and_no_touch_mutation(
    mutation_key: str,
    mutation_value: object,
    expected_blocker: str,
) -> None:
    nci_op08 = _valid_hand_off_nci_op08(_op05_confirmed())
    op01 = _pnt_op01_from_nci_op08(nci_op08)
    mutated = deepcopy(op01)
    mutated[mutation_key] = mutation_value

    op02 = pnt.build_p7_r54_ahr_post_nci_pnt_op02_selected_handoff_or_stop_shape_validation(mutated)

    assert pnt.assert_p7_r54_ahr_post_nci_selected_handoff_or_stop_decision_triage_pnt_op02_selected_handoff_or_stop_shape_validation_contract(op02) is True
    assert op02["pnt_op02_status_ref"] == pnt.P7_R54_AHR_POST_NCI_PNT_OP02_STATUS_BLOCKED_BODYFREE_PROMOTION_AUTORUN_REF
    assert expected_blocker in op02["pnt_op02_blocker_refs"]
    assert op02["next_required_step"] == pnt.P7_R54_AHR_POST_NCI_PNT_NEXT_STEP_BLOCKED_SELECTED_HANDOFF_OR_STOP_SHAPE_REF
    assert op02["selected_handoff_or_stop_executed_here"] is False
    assert op02["p8_start_allowed"] is False
    _assert_r3_no_downstream_execution(op02)


def test_pnt_op03_repairs_when_op02_shape_is_not_valid_for_lane_resolution() -> None:
    nci_op08 = _valid_hand_off_nci_op08(_op05_confirmed())
    op01 = _pnt_op01_from_nci_op08(nci_op08)
    mutated = deepcopy(op01)
    mutated["selected_handoff_or_stop_ref"] = ""
    op02 = pnt.build_p7_r54_ahr_post_nci_pnt_op02_selected_handoff_or_stop_shape_validation(mutated)
    op03 = pnt.build_p7_r54_ahr_post_nci_pnt_op03_selected_handoff_or_stop_lane_consistency_resolver(op02)

    assert pnt.assert_p7_r54_ahr_post_nci_selected_handoff_or_stop_decision_triage_pnt_op03_selected_handoff_or_stop_lane_consistency_resolver_contract(op03) is True
    assert op03["pnt_op03_status_ref"] == pnt.P7_R54_AHR_POST_NCI_PNT_STATUS_REPAIR_BOUNDARY_CANDIDATE_STOPPED_REF
    assert op03["selected_pnt_lane_resolved"] is False
    assert "pnt_op02_shape_not_valid_for_lane_resolver" in op03["pnt_op03_blocker_refs"]
    assert op03["next_required_step"] == pnt.P7_R54_AHR_POST_NCI_PNT_NEXT_STEP_REPAIR_SELECTED_HANDOFF_OR_STOP_LANE_REF
    assert sum(op03[key] is True for key in pnt.P7_R54_AHR_POST_NCI_PNT_OP03_LANE_FLAG_REFS) == 0
    _assert_r3_no_downstream_execution(op03)


def test_pnt_op03_blocks_when_op02_material_contains_body_leak_or_promotion_claim() -> None:
    nci_op08 = _valid_hand_off_nci_op08(_op05_confirmed())
    op02 = _pnt_op02_from_nci_op08(nci_op08)
    mutated = deepcopy(op02)
    mutated["dhr_op05_called_here"] = True
    op03 = pnt.build_p7_r54_ahr_post_nci_pnt_op03_selected_handoff_or_stop_lane_consistency_resolver(mutated)

    assert pnt.assert_p7_r54_ahr_post_nci_selected_handoff_or_stop_decision_triage_pnt_op03_selected_handoff_or_stop_lane_consistency_resolver_contract(op03) is True
    assert op03["pnt_op03_status_ref"] == pnt.P7_R54_AHR_POST_NCI_PNT_STATUS_BLOCKED_BODYFREE_PROMOTION_AUTORUN_STOPPED_REF
    assert op03["selected_pnt_lane_resolved"] is False
    assert "op03_input_promotion_or_autorun_claim_detected" in op03["pnt_op03_blocker_refs"]
    assert op03["next_required_step"] == pnt.P7_R54_AHR_POST_NCI_PNT_NEXT_STEP_BLOCKED_SELECTED_HANDOFF_OR_STOP_LANE_REF
    _assert_r3_no_downstream_execution(op03)


def test_pnt_op02_op03_full_title_aliases_match_short_builders_and_asserts() -> None:
    assert (
        pnt.build_p7_r54_ahr_post_nci_selected_handoff_or_stop_decision_triage_pnt_op02_selected_handoff_or_stop_shape_validation
        is pnt.build_p7_r54_ahr_post_nci_pnt_op02_selected_handoff_or_stop_shape_validation
    )
    assert (
        pnt.assert_p7_r54_ahr_post_nci_selected_handoff_or_stop_decision_triage_pnt_op02_selected_handoff_or_stop_shape_validation_contract
        is pnt.assert_p7_r54_ahr_post_nci_pnt_op02_selected_handoff_or_stop_shape_validation_contract
    )
    assert (
        pnt.build_p7_r54_ahr_post_nci_selected_handoff_or_stop_decision_triage_pnt_op03_selected_handoff_or_stop_lane_consistency_resolver
        is pnt.build_p7_r54_ahr_post_nci_pnt_op03_selected_handoff_or_stop_lane_consistency_resolver
    )
    assert (
        pnt.assert_p7_r54_ahr_post_nci_selected_handoff_or_stop_decision_triage_pnt_op03_selected_handoff_or_stop_lane_consistency_resolver_contract
        is pnt.assert_p7_r54_ahr_post_nci_pnt_op03_selected_handoff_or_stop_lane_consistency_resolver_contract
    )
