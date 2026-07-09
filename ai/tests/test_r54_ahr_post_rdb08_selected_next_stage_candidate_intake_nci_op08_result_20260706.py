# -*- coding: utf-8 -*-
"""R54-AHR Post-RDB08 selected next-stage candidate intake NCI-OP08 closure tests."""

from __future__ import annotations

from copy import deepcopy
from pathlib import Path
import sys

import pytest

TEST_DIR = Path(__file__).resolve().parent
if str(TEST_DIR) not in sys.path:
    sys.path.insert(0, str(TEST_DIR))

import emlis_ai_p7_r54_ahr_post_rdb08_selected_next_stage_candidate_intake_20260706 as nci
import emlis_ai_p7_r54_ahr_post_mrb08_dhr_op04_result_manual_decision_20260705 as rdb
from test_r54_ahr_post_dri_dhr_op04_manual_reintake_mrb_op06_op07_20260705 import (
    _op05_confirmed,
    _op05_invalid_result,
    _op05_not_confirmed,
    _op05_waiting_result,
)
from test_r54_ahr_post_rdb08_selected_next_stage_candidate_intake_nci_op06_op07_20260706 import (
    LANE_FLAG_KEYS,
    _assert_common_bodyfree_no_touch_no_promotion,
    _op03_with_selected_candidate_shape,
    _op04_from_op05,
    _op05_guard_from_op03,
    _op05_guard_from_op05,
    _op06_from_op05_guard,
)


OP08_FORBIDDEN_EXECUTION_KEYS = (
    "dhr_op05_called_here",
    "dhr_op05_builder_called_here",
    "dhr_op06_called_here",
    "dhr_op07_materialized_here",
    "dmd_execution_started_here",
    "r52_actual_execution_started_here",
    "actual_body_full_packet_generated_here",
    "actual_local_human_review_execution_started_here",
    "actual_operation_receipt_created_here",
    "actual_rows_created_here",
    "actual_question_need_observation_rows_created_here",
    "actual_disposal_or_purge_executed_here",
    "p8_question_design_started",
    "p8_question_implementation_started",
    "question_text_materialized",
    "p8_question_substitution_allowed",
)


def _assert_no_downstream_execution(material: dict[str, object]) -> None:
    for key in OP08_FORBIDDEN_EXECUTION_KEYS:
        assert material[key] is False, key
    assert material["p5_final_allowed"] is False
    assert material["p6_start_allowed"] is False
    assert material["p8_start_allowed"] is False
    assert material["release_allowed"] is False
    assert material["full_backend_suite_green_confirmed"] is False
    assert material["rn_contract_green_confirmed"] is False
    assert material["rn_real_device_modal_verified_claimed_here"] is False

TRUE_BOUNDARY_KEYS_OP08 = (
    "dhr_op05_not_called",
    "dhr_op06_not_called",
    "dmd_r52_not_executed",
    "p5_p6_p8_p7_release_not_started",
    "p8_question_design_not_started",
    "p8_question_implementation_not_started",
    "nci_op08_does_not_execute_handoff_or_stop_envelope",
    "nci_op08_does_not_execute_selected_next_stage_candidate",
    "nci_op08_does_not_call_dhr_op05",
    "nci_op08_does_not_call_dhr_op06",
    "nci_op08_does_not_execute_dmd_r52_or_release",
    "nci_op08_does_not_start_actual_review",
    "nci_op08_does_not_request_raw_evidence",
    "nci_op08_does_not_execute_repair",
    "nci_op08_does_not_start_p5_p6_p8_p7_or_release",
    "nci_op08_does_not_materialize_p8_question_spec",
    "nci_op08_does_not_change_api_db_rn_runtime_response_key",
    "full_backend_green_claim_not_made_here",
    "rn_green_claim_not_made_here",
)


def _validation_summary(status: str = "passed") -> dict[str, object]:
    return {
        "schema_version": "nci_op08_validation_summary_bodyfree.v1",
        "body_free": True,
        "validation_summary_ref": "nci_op08_validation_summary_bodyfree",
        "target_test_result_status_ref": status,
        "selected_regression_result_status_ref": status,
        "compileall_result_status_ref": status,
        "combined_run_status_ref": status,
    }


def _result_memo() -> dict[str, object]:
    return {
        "schema_version": "nci_op08_result_memo_bodyfree.v1",
        "body_free": True,
        "result_memo_ref": "nci_op08_bodyfree_result_memo_without_body",
    }


def _chain_from_op05(op05: dict[str, object]) -> tuple[dict[str, object], dict[str, object], dict[str, object], dict[str, object]]:
    op04 = _op04_from_op05(op05)
    op05_guard = _op05_guard_from_op05(op05)
    op06 = _op06_from_op05_guard(op05_guard)
    op07 = nci.build_p7_r54_ahr_post_rdb08_nci_op07_handoff_or_stop_envelope_draft_material(op06)
    return op04, op05_guard, op06, op07


def _chain_from_op03(op03: dict[str, object]) -> tuple[dict[str, object], dict[str, object], dict[str, object], dict[str, object]]:
    op04 = nci.build_p7_r54_ahr_post_rdb08_nci_op04_next_design_target_or_stop_materialization(op03)
    op05_guard = _op05_guard_from_op03(op03)
    op06 = _op06_from_op05_guard(op05_guard)
    op07 = nci.build_p7_r54_ahr_post_rdb08_nci_op07_handoff_or_stop_envelope_draft_material(op06)
    return op04, op05_guard, op06, op07


def _closed_from_chain(
    chain: tuple[dict[str, object], dict[str, object], dict[str, object], dict[str, object]],
    *,
    validation_summary: dict[str, object] | None = None,
    result_memo: dict[str, object] | None = None,
) -> dict[str, object]:
    op04, op05_guard, op06, op07 = chain
    kwargs: dict[str, object] = {
        "next_design_target_or_stop_materialization": op04,
        "bodyfree_no_touch_no_promotion_no_auto_execution_guard": op05_guard,
        "selected_regression_compileall_validation_plan": op06,
        "handoff_or_stop_envelope_draft_material": op07,
    }
    if validation_summary is not None:
        kwargs["validation_summary_bodyfree"] = validation_summary
    if result_memo is not None:
        kwargs["result_memo_bodyfree"] = result_memo
    return nci.build_p7_r54_ahr_post_rdb08_nci_op08_bodyfree_selected_candidate_intake_result_memo_closure(**kwargs)


def _assert_op08_common_contract(material: dict[str, object]) -> None:
    assert set(material) == set(nci.P7_R54_AHR_POST_RDB08_NCI_OP08_REQUIRED_FIELD_REFS)
    assert material["schema_version"] == nci.P7_R54_AHR_POST_RDB08_NCI_OP08_SCHEMA_VERSION
    assert material["operation_step_ref"] == nci.P7_R54_AHR_POST_RDB08_NCI_OP08_STEP_REF
    assert material["nci_op08_status_ref"] == material["bodyfree_selected_candidate_intake_closure_status_ref"]
    assert material["nci_op08_allowed_status_refs"] == list(nci.P7_R54_AHR_POST_RDB08_NCI_OP08_ALLOWED_STATUS_REFS)
    assert material["implemented_steps"] == list(nci.P7_R54_AHR_POST_RDB08_NCI_OP08_IMPLEMENTED_STEPS)
    assert material["not_yet_implemented_steps"] == []
    assert material["validation_command_summary_refs"] == list(nci.P7_R54_AHR_POST_RDB08_NCI_VALIDATION_COMMAND_SUMMARY_REFS)
    assert material["target_test_refs"] == list(nci.P7_R54_AHR_POST_RDB08_NCI_TARGET_TEST_REF_REFS)
    assert material["selected_regression_test_refs"] == list(nci.P7_R54_AHR_POST_RDB08_NCI_SELECTED_REGRESSION_TEST_REF_REFS)
    assert material["compileall_target_refs"] == list(nci.P7_R54_AHR_POST_RDB08_NCI_COMPILEALL_TARGET_REF_REFS)
    for key in TRUE_BOUNDARY_KEYS_OP08:
        assert material[key] is True, key
    assert material["p8_question_substitution_allowed"] is False
    assert material["full_backend_suite_green_confirmed"] is False
    assert material["rn_contract_green_confirmed"] is False
    assert material["rn_real_device_modal_verified_claimed_here"] is False
    assert material["p8_start_allowed"] is False
    assert material["release_allowed"] is False
    assert material["question_text_materialized"] is False
    assert sum(material[key] is True for key in LANE_FLAG_KEYS) == 1
    assert nci.assert_p7_r54_ahr_post_rdb08_nci_op08_bodyfree_selected_candidate_intake_result_memo_closure_contract(material) is True
    _assert_common_bodyfree_no_touch_no_promotion(material)
    _assert_no_downstream_execution(material)


@pytest.mark.parametrize(
    ("op05_factory", "expected_lane", "expected_ref"),
    [
        (_op05_confirmed, nci.P7_R54_AHR_POST_RDB08_NCI_LANE_DHR_OP05_DESIGN_TARGET_REF, nci.P7_R54_AHR_POST_RDB08_NCI_NEXT_DESIGN_DHR_OP05_BOUNDARY_REF),
        (_op05_not_confirmed, nci.P7_R54_AHR_POST_RDB08_NCI_LANE_RETRY_OR_START_ROUTE_REF, nci.P7_R54_AHR_POST_RDB08_NCI_NEXT_DESIGN_RETRY_OR_START_REF),
        (_op05_waiting_result, nci.P7_R54_AHR_POST_RDB08_NCI_LANE_WAIT_EXTERNAL_BODYFREE_CLAIM_REF, nci.P7_R54_AHR_POST_RDB08_NCI_NEXT_DESIGN_WAIT_EXTERNAL_CLAIM_REF),
        (_op05_invalid_result, nci.P7_R54_AHR_POST_RDB08_NCI_LANE_REPAIR_RDB_OR_UPSTREAM_RESULT_REF, nci.P7_R54_AHR_POST_RDB08_NCI_NEXT_DESIGN_REPAIR_BOUNDARY_REF),
    ],
)
def test_nci_op08_closes_handoff_lanes_bodyfree_without_executing_candidate(
    op05_factory,
    expected_lane: str,
    expected_ref: str,
) -> None:
    material = _closed_from_chain(
        _chain_from_op05(op05_factory()),
        validation_summary=_validation_summary(),
        result_memo=_result_memo(),
    )

    assert material["nci_op08_status_ref"] == nci.P7_R54_AHR_POST_RDB08_NCI_OP08_STATUS_CLOSED_BODYFREE_STOPPED_REF
    assert material["nci_op08_closed_bodyfree_stopped"] is True
    assert material["op04_contract_valid"] is True
    assert material["op05_contract_valid"] is True
    assert material["op06_contract_valid"] is True
    assert material["op07_contract_valid"] is True
    assert material["op07_ready_for_op08"] is True
    assert material["validation_summary_bodyfree_accepted"] is True
    assert material["result_memo_bodyfree_accepted"] is True
    assert material["selected_nci_lane_ref"] == expected_lane
    assert material["selected_handoff_or_stop_ref"] == expected_ref
    assert material["selected_handoff_or_stop_not_executed"] is True
    assert material["selected_next_design_or_stop_not_executed"] is True
    assert material["rdb08_selected_next_stage_candidate_not_executed"] is True
    assert material["next_required_step"] == expected_ref
    assert material["nci_target_green_confirmed"] is True
    assert material["selected_regression_green_confirmed"] is True
    assert material["compileall_green_confirmed"] is True
    assert material["nci_op08_blocker_refs"] == []
    _assert_op08_common_contract(material)


def test_nci_op08_closes_manual_hold_and_blocked_lanes_as_stop_envelopes_without_promotion() -> None:
    unresolved_op03 = _op03_with_selected_candidate_shape(
        rdb_status_ref=rdb.P7_R54_AHR_POST_MRB08_RDB_STATUS_INCOMPLETE_UNRESOLVED_MANUAL_HOLD_STOPPED_REF,
        candidate_ref=rdb.P7_R54_AHR_POST_MRB08_RDB_NEXT_STEP_MANUAL_HOLD_UNRESOLVED_REF,
        candidate_kind_ref=rdb.P7_R54_AHR_POST_MRB08_RDB_CANDIDATE_KIND_UNRESOLVED_REF,
        decision_lane_ref=rdb.P7_R54_AHR_POST_MRB08_RDB_DECISION_LANE_MANUAL_HOLD_UNRESOLVED_REF,
    )
    blocked_op03 = _op03_with_selected_candidate_shape(
        rdb_status_ref=rdb.P7_R54_AHR_POST_MRB08_RDB_STATUS_BLOCKED_BODYFREE_LEAK_PROMOTION_OR_AUTORUN_REF,
        candidate_ref=rdb.P7_R54_AHR_POST_MRB08_RDB_NEXT_STEP_BLOCKED_POST_MRB08_REF,
        candidate_kind_ref=rdb.P7_R54_AHR_POST_MRB08_RDB_CANDIDATE_KIND_BLOCKED_REF,
        decision_lane_ref=rdb.P7_R54_AHR_POST_MRB08_RDB_DECISION_LANE_BLOCKED_REF,
    )

    for op03, expected_lane, expected_ref in (
        (unresolved_op03, nci.P7_R54_AHR_POST_RDB08_NCI_LANE_MANUAL_HOLD_UNRESOLVED_REF, nci.P7_R54_AHR_POST_RDB08_NCI_NEXT_STOP_MANUAL_HOLD_REF),
        (blocked_op03, nci.P7_R54_AHR_POST_RDB08_NCI_LANE_BLOCKED_BODYFREE_PROMOTION_AUTORUN_REF, nci.P7_R54_AHR_POST_RDB08_NCI_NEXT_STOP_BLOCKED_REF),
    ):
        material = _closed_from_chain(_chain_from_op03(op03), validation_summary=_validation_summary(), result_memo=_result_memo())
        assert material["nci_op08_status_ref"] == nci.P7_R54_AHR_POST_RDB08_NCI_OP08_STATUS_CLOSED_BODYFREE_STOPPED_REF
        assert material["selected_nci_lane_ref"] == expected_lane
        assert material["selected_handoff_or_stop_ref"] == expected_ref
        assert material["selected_handoff_or_stop_kind_ref"] == nci.P7_R54_AHR_POST_RDB08_NCI_OP07_STOP_ENVELOPE_KIND_REF
        assert material["selected_handoff_or_stop_not_executed"] is True
        assert material["next_required_step"] == expected_ref
        _assert_op08_common_contract(material)


def test_nci_op08_waits_when_validation_or_result_memo_refs_are_missing() -> None:
    material = _closed_from_chain(_chain_from_op05(_op05_confirmed()))

    assert material["nci_op08_status_ref"] == nci.P7_R54_AHR_POST_RDB08_NCI_OP08_STATUS_WAITING_FOR_INPUT_REFS_REF
    assert material["nci_op08_waiting_for_input_refs"] is True
    assert material["validation_summary_bodyfree_present"] is False
    assert material["result_memo_bodyfree_present"] is False
    assert material["selected_handoff_or_stop_not_executed"] is False
    assert material["next_required_step"] == nci.P7_R54_AHR_POST_RDB08_NCI_OP08_NEXT_STEP_WAIT_REF
    assert "validation_summary_bodyfree_missing" in material["nci_op08_blocker_refs"]
    assert "result_memo_bodyfree_missing" in material["nci_op08_blocker_refs"]
    _assert_op08_common_contract(material)


def test_nci_op08_repairs_invalid_op07_envelope_without_executing_repair() -> None:
    op04, op05_guard, op06, op07 = _chain_from_op05(_op05_confirmed())
    invalid_op07 = deepcopy(op07)
    invalid_op07["next_required_step"] = "incorrect_next_required_step"

    material = nci.build_p7_r54_ahr_post_rdb08_nci_op08_bodyfree_selected_candidate_intake_result_memo_closure(
        next_design_target_or_stop_materialization=op04,
        bodyfree_no_touch_no_promotion_no_auto_execution_guard=op05_guard,
        selected_regression_compileall_validation_plan=op06,
        handoff_or_stop_envelope_draft_material=invalid_op07,
        validation_summary_bodyfree=_validation_summary(),
        result_memo_bodyfree=_result_memo(),
    )

    assert material["nci_op08_status_ref"] == nci.P7_R54_AHR_POST_RDB08_NCI_OP08_STATUS_REPAIR_REQUIRED_REF
    assert material["nci_op08_repair_required"] is True
    assert "nci_op07_contract_invalid" in material["nci_op08_blocker_refs"]
    assert material["selected_handoff_or_stop_not_executed"] is False
    assert material["next_required_step"] == nci.P7_R54_AHR_POST_RDB08_NCI_OP08_NEXT_STEP_REPAIR_REF
    _assert_op08_common_contract(material)


@pytest.mark.parametrize(
    "mutation_target, mutation_key, mutation_value, expected_blocker",
    [
        ("validation", "question_text", "blocked_question", "nci_op08_validation_summary_forbidden_payload_key_detected"),
        ("memo", "stdout", "blocked_terminal_body", "nci_op08_result_memo_forbidden_payload_key_detected"),
        ("op07", "dhr_op05_called_here", True, "nci_op07_promotion_or_autorun_claim_detected_before_result_memo_closure"),
        ("op07", "changed_file_refs", ["Cocolon/tests/rn-screen-contracts.test.js"], "nci_op07_api_db_rn_runtime_response_key_or_p8_question_touch_detected_before_result_memo_closure"),
    ],
)
def test_nci_op08_blocks_bodyfree_no_touch_promotion_or_autorun_claims(
    mutation_target: str,
    mutation_key: str,
    mutation_value: object,
    expected_blocker: str,
) -> None:
    op04, op05_guard, op06, op07 = _chain_from_op05(_op05_confirmed())
    validation_summary = _validation_summary()
    result_memo = _result_memo()
    if mutation_target == "validation":
        validation_summary[mutation_key] = mutation_value
    elif mutation_target == "memo":
        result_memo[mutation_key] = mutation_value
    else:
        op07 = deepcopy(op07)
        op07[mutation_key] = mutation_value

    material = nci.build_p7_r54_ahr_post_rdb08_nci_op08_bodyfree_selected_candidate_intake_result_memo_closure(
        next_design_target_or_stop_materialization=op04,
        bodyfree_no_touch_no_promotion_no_auto_execution_guard=op05_guard,
        selected_regression_compileall_validation_plan=op06,
        handoff_or_stop_envelope_draft_material=op07,
        validation_summary_bodyfree=validation_summary,
        result_memo_bodyfree=result_memo,
    )

    assert material["nci_op08_status_ref"] == nci.P7_R54_AHR_POST_RDB08_NCI_OP08_STATUS_BLOCKED_BODYFREE_PROMOTION_AUTORUN_REF
    assert material["nci_op08_blocked_bodyfree_promotion_autorun"] is True
    assert expected_blocker in material["nci_op08_blocker_refs"]
    assert material["selected_handoff_or_stop_not_executed"] is False
    assert material["next_required_step"] == nci.P7_R54_AHR_POST_RDB08_NCI_OP08_NEXT_STEP_BLOCKED_REF
    _assert_op08_common_contract(material)


@pytest.mark.parametrize(
    ("mutation_key", "mutation_value"),
    [
        ("dhr_op05_builder_called_here", True),
        ("p8_start_allowed", True),
        ("release_allowed", True),
        ("rn_contract_green_confirmed", True),
        ("question_text_materialized", True),
    ],
)
def test_nci_op08_contract_rejects_execution_p8_release_or_rn_claim_mutations(
    mutation_key: str,
    mutation_value: object,
) -> None:
    material = _closed_from_chain(_chain_from_op05(_op05_confirmed()), validation_summary=_validation_summary(), result_memo=_result_memo())
    mutated = deepcopy(material)
    mutated[mutation_key] = mutation_value
    with pytest.raises(ValueError):
        nci.assert_p7_r54_ahr_post_rdb08_nci_op08_bodyfree_selected_candidate_intake_result_memo_closure_contract(mutated)


def test_nci_op08_full_title_aliases_match_short_builders_and_asserts() -> None:
    assert (
        nci.build_p7_r54_ahr_post_rdb08_selected_next_stage_candidate_intake_nci_op08_bodyfree_selected_candidate_intake_result_memo_closure
        is nci.build_p7_r54_ahr_post_rdb08_nci_op08_bodyfree_selected_candidate_intake_result_memo_closure
    )
    assert (
        nci.assert_p7_r54_ahr_post_rdb08_selected_next_stage_candidate_intake_nci_op08_bodyfree_selected_candidate_intake_result_memo_closure_contract
        is nci.assert_p7_r54_ahr_post_rdb08_nci_op08_bodyfree_selected_candidate_intake_result_memo_closure_contract
    )
