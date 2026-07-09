# -*- coding: utf-8 -*-
"""R54-AHR Post-NCI selected handoff-or-stop decision triage PNT-OP00/OP01 tests."""

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
from test_r54_ahr_post_rdb08_selected_next_stage_candidate_intake_nci_op08_result_20260706 import (
    _chain_from_op05,
    _closed_from_chain,
    _op05_confirmed,
    _result_memo,
    _validation_summary,
)


PNT_R2_FORBIDDEN_EXECUTION_KEYS = (
    "selected_handoff_or_stop_executed_here",
    "handoff_or_stop_envelope_executed_here",
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


def _valid_closed_nci_op08() -> dict[str, object]:
    return _closed_from_chain(
        _chain_from_op05(_op05_confirmed()),
        validation_summary=_validation_summary(),
        result_memo=_result_memo(),
    )


def _waiting_nci_op08() -> dict[str, object]:
    return _closed_from_chain(_chain_from_op05(_op05_confirmed()))


def _repair_nci_op08() -> dict[str, object]:
    op04, op05_guard, op06, op07 = _chain_from_op05(_op05_confirmed())
    invalid_op07 = deepcopy(op07)
    invalid_op07["next_required_step"] = "incorrect_next_required_step"
    return nci.build_p7_r54_ahr_post_rdb08_nci_op08_bodyfree_selected_candidate_intake_result_memo_closure(
        next_design_target_or_stop_materialization=op04,
        bodyfree_no_touch_no_promotion_no_auto_execution_guard=op05_guard,
        selected_regression_compileall_validation_plan=op06,
        handoff_or_stop_envelope_draft_material=invalid_op07,
        validation_summary_bodyfree=_validation_summary(),
        result_memo_bodyfree=_result_memo(),
    )


def _blocked_nci_op08() -> dict[str, object]:
    op04, op05_guard, op06, op07 = _chain_from_op05(_op05_confirmed())
    blocked_op07 = deepcopy(op07)
    blocked_op07["dhr_op05_called_here"] = True
    return nci.build_p7_r54_ahr_post_rdb08_nci_op08_bodyfree_selected_candidate_intake_result_memo_closure(
        next_design_target_or_stop_materialization=op04,
        bodyfree_no_touch_no_promotion_no_auto_execution_guard=op05_guard,
        selected_regression_compileall_validation_plan=op06,
        handoff_or_stop_envelope_draft_material=blocked_op07,
        validation_summary_bodyfree=_validation_summary(),
        result_memo_bodyfree=_result_memo(),
    )


def _assert_r2_no_downstream_execution(material: dict[str, object]) -> None:
    for key in PNT_R2_FORBIDDEN_EXECUTION_KEYS:
        assert material[key] is False, key
    assert material["git_connection_required"] is False
    assert material["git_checked"] is False
    assert material["body_free"] is True


def test_pnt_r2_keeps_r0_r1_helper_skeleton_and_constants_available() -> None:
    summary = pnt.build_p7_r54_ahr_post_nci_pnt_r1_helper_skeleton_constants_summary()

    assert pnt.assert_p7_r54_ahr_post_nci_pnt_r1_helper_skeleton_constants_summary_contract(summary) is True
    assert summary["explicit_nci_op08_material_required"] is True
    assert summary["nci_op08_default_builder_call_allowed"] is False
    assert summary["nci_op08_default_material_synthesis_allowed"] is False
    assert pnt.P7_R54_AHR_POST_NCI_PNT_OP00_STEP_REF in summary["pnt_step_refs"]
    assert pnt.P7_R54_AHR_POST_NCI_PNT_OP01_STEP_REF in summary["pnt_step_refs"]
    _assert_r2_no_downstream_execution(summary)


def test_pnt_op00_refreezes_scope_explicit_input_and_no_execution_boundary() -> None:
    material = pnt.build_p7_r54_ahr_post_nci_pnt_op00_scope_explicit_input_no_execution_refreeze_after_nci_op08()

    assert pnt.assert_p7_r54_ahr_post_nci_pnt_op00_scope_explicit_input_no_execution_refreeze_after_nci_op08_contract(material) is True
    assert set(material) == set(pnt.P7_R54_AHR_POST_NCI_PNT_OP00_REQUIRED_FIELD_REFS)
    assert material["operation_step_ref"] == pnt.P7_R54_AHR_POST_NCI_PNT_OP00_STEP_REF
    assert material["pnt_scope_refrozen"] is True
    assert material["explicit_nci_op08_material_required"] is True
    assert material["nci_op08_default_builder_call_allowed"] is False
    assert material["pnt_op00_does_not_intake_nci_op08_material"] is True
    assert material["pnt_op00_does_not_synthesize_nci_op08_material"] is True
    assert material["next_required_step"] == pnt.P7_R54_AHR_POST_NCI_PNT_OP01_STEP_REF
    _assert_r2_no_downstream_execution(material)


@pytest.mark.parametrize("mutation_key", ["api_changed", "db_changed", "rn_changed", "response_key_changed"])
def test_pnt_op00_contract_rejects_public_contract_mutation_claims(mutation_key: str) -> None:
    material = pnt.build_p7_r54_ahr_post_nci_pnt_op00_scope_explicit_input_no_execution_refreeze_after_nci_op08()
    mutated = deepcopy(material)
    mutated[mutation_key] = True

    with pytest.raises(ValueError):
        pnt.assert_p7_r54_ahr_post_nci_pnt_op00_scope_explicit_input_no_execution_refreeze_after_nci_op08_contract(mutated)


def test_pnt_op01_waits_when_explicit_nci_op08_material_is_missing_without_default_builder() -> None:
    material = pnt.build_p7_r54_ahr_post_nci_pnt_op01_explicit_nci_op08_bodyfree_result_memo_closure_intake()

    assert pnt.assert_p7_r54_ahr_post_nci_pnt_op01_explicit_nci_op08_bodyfree_result_memo_closure_intake_contract(material) is True
    assert material["pnt_op01_status_ref"] == pnt.P7_R54_AHR_POST_NCI_PNT_OP01_STATUS_WAITING_FOR_EXPLICIT_NCI_OP08_CLOSURE_REF
    assert material["nci_op08_material_present"] is False
    assert material["nci_op08_contract_valid"] is False
    assert material["nci_op08_default_builder_called_here"] is False
    assert material["nci_op08_default_material_synthesized_here"] is False
    assert material["next_required_step"] == pnt.P7_R54_AHR_POST_NCI_PNT_NEXT_STEP_WAIT_FOR_EXPLICIT_NCI_OP08_CLOSURE_REF
    assert "explicit_nci_op08_bodyfree_result_memo_closure_missing" in material["pnt_op01_blocker_refs"]
    _assert_r2_no_downstream_execution(material)


def test_pnt_op01_accepts_valid_explicit_nci_op08_closure_without_classifying_next_boundary() -> None:
    nci_op08 = _valid_closed_nci_op08()
    material = pnt.build_p7_r54_ahr_post_nci_pnt_op01_explicit_nci_op08_bodyfree_result_memo_closure_intake(
        nci_op08_bodyfree_selected_candidate_intake_result_memo_closure=nci_op08,
    )

    assert pnt.assert_p7_r54_ahr_post_nci_pnt_op01_explicit_nci_op08_bodyfree_result_memo_closure_intake_contract(material) is True
    assert material["pnt_op01_status_ref"] == pnt.P7_R54_AHR_POST_NCI_PNT_OP01_STATUS_READY_FOR_OP02_REF
    assert material["pnt_op01_ready_for_handoff_or_stop_shape_validation"] is True
    assert material["next_required_step"] == pnt.P7_R54_AHR_POST_NCI_PNT_OP02_STEP_REF
    assert material["nci_op08_material_present"] is True
    assert material["nci_op08_contract_valid"] is True
    assert material["nci_op08_closed_bodyfree_stopped"] is True
    assert material["selected_handoff_or_stop_ref_present"] is True
    assert material["selected_handoff_or_stop_not_executed"] is True
    assert material["pnt_op01_does_not_validate_selected_handoff_or_stop_shape"] is True
    assert material["pnt_op01_does_not_resolve_selected_handoff_or_stop_lane"] is True
    assert material["pnt_op01_does_not_materialize_next_boundary_selection"] is True
    assert material["pnt_op01_blocker_refs"] == []
    _assert_r2_no_downstream_execution(material)


@pytest.mark.parametrize(
    ("factory", "expected_status", "expected_next", "expected_blocker"),
    [
        (
            _waiting_nci_op08,
            pnt.P7_R54_AHR_POST_NCI_PNT_OP01_STATUS_WAITING_FOR_NCI_OP08_TO_CLOSE_REF,
            pnt.P7_R54_AHR_POST_NCI_PNT_NEXT_STEP_WAIT_FOR_NCI_OP08_CLOSURE_REF,
            "nci_op08_waiting_for_input_refs",
        ),
        (
            _repair_nci_op08,
            pnt.P7_R54_AHR_POST_NCI_PNT_OP01_STATUS_REPAIR_NCI_OP08_REF,
            pnt.P7_R54_AHR_POST_NCI_PNT_NEXT_STEP_REPAIR_NCI_OP08_CLOSURE_REF,
            "nci_op08_repair_required_for_closure_inputs",
        ),
        (
            _blocked_nci_op08,
            pnt.P7_R54_AHR_POST_NCI_PNT_OP01_STATUS_BLOCKED_NCI_OP08_REF,
            pnt.P7_R54_AHR_POST_NCI_PNT_NEXT_STEP_BLOCKED_NCI_OP08_CLOSURE_REF,
            "nci_op08_status_bodyfree_leak_promotion_or_autorun_blocked",
        ),
    ],
)
def test_pnt_op01_keeps_waiting_repair_and_blocked_nci_op08_as_non_promoting_states(
    factory,
    expected_status: str,
    expected_next: str,
    expected_blocker: str,
) -> None:
    nci_op08 = factory()
    material = pnt.build_p7_r54_ahr_post_nci_pnt_op01_explicit_nci_op08_bodyfree_result_memo_closure_intake(
        nci_op08_bodyfree_selected_candidate_intake_result_memo_closure=nci_op08,
    )

    assert pnt.assert_p7_r54_ahr_post_nci_pnt_op01_explicit_nci_op08_bodyfree_result_memo_closure_intake_contract(material) is True
    assert material["pnt_op01_status_ref"] == expected_status
    assert material["next_required_step"] == expected_next
    assert expected_blocker in material["pnt_op01_blocker_refs"]
    assert material["pnt_op01_ready_for_handoff_or_stop_shape_validation"] is False
    assert material["selected_handoff_or_stop_executed_here"] is False
    assert material["dhr_op05_called_here"] is False
    assert material["p8_start_allowed"] is False
    _assert_r2_no_downstream_execution(material)


@pytest.mark.parametrize(
    ("mutation_key", "mutation_value", "expected_blocker"),
    [
        ("raw_evidence", "blocked_raw_evidence", "nci_op08_input_forbidden_payload_key_detected"),
        ("question_text", "blocked_question_text", "nci_op08_input_forbidden_payload_key_detected"),
        ("dhr_op05_called_here", True, "nci_op08_input_promotion_or_autorun_claim_detected"),
        ("api_changed", True, "nci_op08_input_api_db_rn_runtime_response_key_or_p8_question_touch_detected"),
    ],
)
def test_pnt_op01_blocks_body_leak_promotion_or_no_touch_mutation_in_explicit_nci_material(
    mutation_key: str,
    mutation_value: object,
    expected_blocker: str,
) -> None:
    nci_op08 = _valid_closed_nci_op08()
    mutated = deepcopy(nci_op08)
    mutated[mutation_key] = mutation_value

    material = pnt.build_p7_r54_ahr_post_nci_pnt_op01_explicit_nci_op08_bodyfree_result_memo_closure_intake(
        nci_op08_bodyfree_selected_candidate_intake_result_memo_closure=mutated,
    )

    assert pnt.assert_p7_r54_ahr_post_nci_pnt_op01_explicit_nci_op08_bodyfree_result_memo_closure_intake_contract(material) is True
    assert material["pnt_op01_status_ref"] == pnt.P7_R54_AHR_POST_NCI_PNT_OP01_STATUS_BLOCKED_NCI_OP08_REF
    assert material["next_required_step"] == pnt.P7_R54_AHR_POST_NCI_PNT_NEXT_STEP_BLOCKED_NCI_OP08_CLOSURE_REF
    assert expected_blocker in material["pnt_op01_blocker_refs"]
    assert material["pnt_op01_ready_for_handoff_or_stop_shape_validation"] is False
    _assert_r2_no_downstream_execution(material)


def test_pnt_op01_full_title_aliases_match_short_builders_and_asserts() -> None:
    assert (
        pnt.build_p7_r54_ahr_post_nci_selected_handoff_or_stop_decision_triage_pnt_op00_scope_explicit_input_no_execution_refreeze_after_nci_op08
        is pnt.build_p7_r54_ahr_post_nci_pnt_op00_scope_explicit_input_no_execution_refreeze_after_nci_op08
    )
    assert (
        pnt.assert_p7_r54_ahr_post_nci_selected_handoff_or_stop_decision_triage_pnt_op00_scope_explicit_input_no_execution_refreeze_after_nci_op08_contract
        is pnt.assert_p7_r54_ahr_post_nci_pnt_op00_scope_explicit_input_no_execution_refreeze_after_nci_op08_contract
    )
    assert (
        pnt.build_p7_r54_ahr_post_nci_selected_handoff_or_stop_decision_triage_pnt_op01_explicit_nci_op08_bodyfree_result_memo_closure_intake
        is pnt.build_p7_r54_ahr_post_nci_pnt_op01_explicit_nci_op08_bodyfree_result_memo_closure_intake
    )
    assert (
        pnt.assert_p7_r54_ahr_post_nci_selected_handoff_or_stop_decision_triage_pnt_op01_explicit_nci_op08_bodyfree_result_memo_closure_intake_contract
        is pnt.assert_p7_r54_ahr_post_nci_pnt_op01_explicit_nci_op08_bodyfree_result_memo_closure_intake_contract
    )
