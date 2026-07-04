# -*- coding: utf-8 -*-
"""R54-AHR Post-PMN23 downstream manual decision hold DMH-OP00/OP01 tests."""

from __future__ import annotations

from copy import deepcopy
from pathlib import Path
import sys

import pytest

TEST_DIR = Path(__file__).resolve().parent
if str(TEST_DIR) not in sys.path:
    sys.path.insert(0, str(TEST_DIR))

import emlis_ai_p7_r54_ahr_post_pmn23_downstream_manual_decision_hold_evidence_intake_20260701 as dmh
import emlis_ai_p7_r54_ahr_post_mn11_actual_local_only_human_review_operation_20260630 as pmn
import test_r54_ahr_post_mn11_actual_local_only_human_review_operation_pmn_op22_op23_contract_20260630 as pmn_op23_prev


def _ready_pmn_op23() -> dict[str, object]:
    material = pmn_op23_prev._ready_op23()
    assert pmn.assert_p7_r54_ahr_post_mn11_pmn_op23_acceptance_fail_closed_finalizer_contract(material) is True
    return material


def _status_envelope() -> dict[str, object]:
    return dmh.build_p7_r54_ahr_post_pmn23_dmh_pmn_op23_result_memo_current_status_envelope_bodyfree()


def _ready_op00() -> dict[str, object]:
    material = dmh.build_p7_r54_ahr_post_pmn23_dmh_op00_scope_no_touch_no_promotion_refreeze()
    assert dmh.assert_p7_r54_ahr_post_pmn23_dmh_op00_scope_no_touch_no_promotion_refreeze_contract(material) is True
    return material


def _ready_op01() -> dict[str, object]:
    material = dmh.build_p7_r54_ahr_post_pmn23_dmh_op01_pmn_op23_downstream_manual_decision_hold_intake(
        scope_no_touch_no_promotion_refreeze=_ready_op00(),
        pmn_op23_acceptance_fail_closed_finalizer=_ready_pmn_op23(),
        pmn_op23_result_memo_current_status=_status_envelope(),
    )
    assert dmh.assert_p7_r54_ahr_post_pmn23_dmh_op01_pmn_op23_downstream_manual_decision_hold_intake_contract(material) is True
    return material


def _assert_bodyfree_no_touch_no_promotion(material: dict[str, object]) -> None:
    assert material["body_free"] is True
    for key in dmh.P7_R54_AHR_POST_PMN23_DMH_REQUIRED_FALSE_FLAG_REFS:
        assert material[key] is False, key
    for marker_map_key in ("public_contract", "post_pmn23_no_touch_contract", "body_free_markers"):
        assert material[marker_map_key]
        assert all(value is False for value in material[marker_map_key].values()), marker_map_key
    assert all(value is False for value in material["not_claimed_boundary"].values())
    for forbidden_key in dmh.P7_R54_AHR_POST_PMN23_DMH_FORBIDDEN_PAYLOAD_KEY_REFS:
        assert forbidden_key not in material, forbidden_key


def test_dmh_op00_refreezes_scope_no_touch_and_no_promotion_without_intake_or_execution() -> None:
    material = _ready_op00()

    assert set(material) == set(dmh.P7_R54_AHR_POST_PMN23_DMH_OP00_REQUIRED_FIELD_REFS)
    assert material["schema_version"] == dmh.P7_R54_AHR_POST_PMN23_DMH_OP00_SCOPE_NO_TOUCH_NO_PROMOTION_REFREEZE_SCHEMA_VERSION
    assert material["operation_step_ref"] == dmh.P7_R54_AHR_POST_PMN23_DMH_OP00_STEP_REF
    assert material["chosen_stage_ref"] == dmh.P7_R54_AHR_POST_PMN23_DMH_CHOSEN_STAGE_REF
    assert tuple(material["not_stage_refs"]) == dmh.P7_R54_AHR_POST_PMN23_DMH_NOT_STAGE_REFS
    assert material["post_pmn23_dmh_scope_confirmed"] is True
    assert material["actual_local_only_human_review_evidence_intake_entry"] is True
    assert material["no_touch_boundary_confirmed"] is True
    assert material["no_promotion_boundary_confirmed"] is True
    assert material["dmh_op00_does_not_intake_pmn_op23_hold"] is True
    assert material["dmh_op00_does_not_generate_body_full_packet"] is True
    assert material["dmh_op00_does_not_run_actual_human_review"] is True
    assert material["dmh_op00_does_not_create_operation_receipt_or_rows_or_disposal"] is True
    assert material["pmn_op23_acceptance_not_promoted_to_actual_review_evidence_complete"] is True
    assert material["p8_question_design_out_of_scope"] is True
    assert material["p8_question_implementation_out_of_scope"] is True
    assert material["p6_start_out_of_scope"] is True
    assert material["r52_actual_execution_out_of_scope"] is True
    assert material["p5_finalization_out_of_scope"] is True
    assert material["p7_complete_out_of_scope"] is True
    assert material["release_decision_out_of_scope"] is True
    assert material["required_case_count"] == 24
    assert material["actual_review_basis_ref"] == dmh.P7_R54_AHR_POST_PMN23_DMH_ACTUAL_REVIEW_BASIS_REF
    assert material["local_received_zip_refs_are_actual_review_basis"] is False
    assert material["local_received_zip_refs_used_to_rewrite_current_actual_review_basis"] is False
    assert tuple(material["implemented_steps"]) == dmh.P7_R54_AHR_POST_PMN23_DMH_OP00_IMPLEMENTED_STEPS
    assert tuple(material["not_yet_implemented_steps"]) == dmh.P7_R54_AHR_POST_PMN23_DMH_OP00_NOT_YET_IMPLEMENTED_STEPS
    assert material["next_required_step"] == dmh.P7_R54_AHR_POST_PMN23_DMH_OP01_STEP_REF
    _assert_bodyfree_no_touch_no_promotion(material)


@pytest.mark.parametrize(
    ("field", "bad_value"),
    [
        ("post_pmn23_dmh_scope_confirmed", False),
        ("actual_local_only_human_review_evidence_intake_entry", False),
        ("no_touch_boundary_confirmed", False),
        ("no_promotion_boundary_confirmed", False),
        ("pmn_op23_acceptance_not_promoted_to_actual_review_evidence_complete", False),
        ("p8_question_design_out_of_scope", False),
        ("release_decision_out_of_scope", False),
        ("actual_review_evidence_complete_from_real_review", True),
        ("p8_start_allowed", True),
        ("actual_r52_reintake_execution_confirmed", True),
        ("release_allowed", True),
    ],
)
def test_dmh_op00_contract_rejects_scope_or_promotion_mutation(field: str, bad_value: object) -> None:
    material = _ready_op00()
    mutated = deepcopy(material)
    mutated[field] = bad_value

    with pytest.raises(ValueError):
        dmh.assert_p7_r54_ahr_post_pmn23_dmh_op00_scope_no_touch_no_promotion_refreeze_contract(mutated)


def test_dmh_op01_blocks_until_pmn_op23_and_result_memo_current_status_are_supplied() -> None:
    material = dmh.build_p7_r54_ahr_post_pmn23_dmh_op01_pmn_op23_downstream_manual_decision_hold_intake(
        scope_no_touch_no_promotion_refreeze=_ready_op00(),
    )

    assert set(material) == set(dmh.P7_R54_AHR_POST_PMN23_DMH_OP01_REQUIRED_FIELD_REFS)
    assert material["dmh_op01_status_ref"] == dmh.P7_R54_AHR_POST_PMN23_DMH_OP01_BLOCKED_STATUS_REF
    assert material["dmh_op01_ready"] is False
    assert "dmh_op01_pmn_op23_acceptance_finalizer_missing" in material["dmh_op01_blocker_refs"]
    assert "dmh_op01_pmn_op23_result_memo_current_status_missing" in material["dmh_op01_blocker_refs"]
    assert material["pmn_op23_acceptance_finalizer_present"] is False
    assert material["pmn_op23_result_memo_current_status_present"] is False
    assert material["dmh_op01_passes_to_existing_pmn_postcr22_ex_reuse_decision"] is False
    assert material["actual_local_only_human_review_evidence_intake_required_before_downstream_decision"] is False
    assert material["next_required_step"] == dmh.P7_R54_AHR_POST_PMN23_DMH_OP01_BLOCKED_NEXT_REQUIRED_STEP_REF
    assert dmh.assert_p7_r54_ahr_post_pmn23_dmh_op01_pmn_op23_downstream_manual_decision_hold_intake_contract(material) is True
    _assert_bodyfree_no_touch_no_promotion(material)


def test_dmh_op01_intakes_pmn_op23_downstream_hold_without_promoting_contract_fixture_completion() -> None:
    material = _ready_op01()

    assert set(material) == set(dmh.P7_R54_AHR_POST_PMN23_DMH_OP01_REQUIRED_FIELD_REFS)
    assert material["schema_version"] == dmh.P7_R54_AHR_POST_PMN23_DMH_OP01_PMN_OP23_DOWNSTREAM_MANUAL_DECISION_HOLD_INTAKE_SCHEMA_VERSION
    assert material["operation_step_ref"] == dmh.P7_R54_AHR_POST_PMN23_DMH_OP01_STEP_REF
    assert material["dmh_op01_status_ref"] == dmh.P7_R54_AHR_POST_PMN23_DMH_OP01_READY_STATUS_REF
    assert material["dmh_op01_ready"] is True
    assert material["dmh_op01_blocker_refs"] == []
    assert material["dmh_op01_reason_refs"] == ["dmh_op01_pmn_op23_hold_and_real_evidence_missing_status_confirmed_bodyfree"]
    assert material["pmn_op23_result_memo_current_status_present"] is True
    assert material["pmn_op23_acceptance_finalizer_present"] is True
    assert material["pmn_op23_contract_valid"] is True
    assert material["pmn_op23_acceptance_finalizer_ready"] is True
    assert material["pmn_op23_next_required_step"] == dmh.P7_R54_AHR_POST_PMN23_DMH_DOWNSTREAM_MANUAL_DECISION_HOLD_REF
    assert material["pmn_op23_next_required_step_confirmed"] is True
    assert material["pmn_op23_downstream_manual_decision_hold_confirmed"] is True
    assert material["pmn_op23_actual_review_basis_ref_confirmed"] is True
    assert material["pmn_op23_current_actual_review_basis_remains_264_85_258_171"] is True
    assert material["pmn_op23_contract_fixture_complete_flag_observed"] is True
    assert material["pmn_op23_contract_fixture_complete_flag_not_promoted_to_actual_evidence"] is True
    assert material["actual_review_evidence_status_ref"] == dmh.P7_R54_AHR_POST_PMN23_DMH_ACTUAL_REVIEW_EVIDENCE_STATUS_REF
    assert material["actual_review_evidence_status_missing_real_review_required_confirmed"] is True
    assert material["actual_review_evidence_complete_from_contract_fixture_path"] is True
    assert material["actual_review_evidence_complete_from_real_review_current_status"] is False
    assert material["actual_review_evidence_complete_from_real_review_false_confirmed"] is True
    assert material["actual_review_evidence_complete_from_real_operation_claimed"] is False
    assert material["actual_body_full_packet_generation_status_ref"] == "not_run"
    assert material["actual_local_human_review_execution_status_ref"] == "not_run"
    assert material["actual_operation_receipt_status_ref"] == "not_received"
    assert material["actual_sanitized_review_result_rows_status_ref"] == "not_received"
    assert material["actual_rating_rows_status_ref"] == "not_received"
    assert material["actual_question_need_observation_rows_status_ref"] == "not_received"
    assert material["actual_disposal_purge_status_ref"] == "not_run"
    assert material["pmn_op23_green_is_not_actual_human_review_complete"] is True
    assert material["pmn_op23_acceptance_is_not_actual_operation_receipt"] is True
    assert material["dmh_op01_does_not_treat_pmn_op23_green_as_real_review_complete"] is True
    assert material["dmh_op01_does_not_generate_body_full_packet"] is True
    assert material["dmh_op01_does_not_run_actual_human_review"] is True
    assert material["dmh_op01_does_not_create_operation_receipt_or_rows_or_disposal"] is True
    assert material["dmh_op01_does_not_start_p8_p6_r52_or_release"] is True
    assert material["dmh_op01_passes_to_existing_pmn_postcr22_ex_reuse_decision"] is True
    assert material["actual_local_only_human_review_evidence_intake_required_before_downstream_decision"] is True
    assert material["basis_rewritten_here"] is False
    assert material["local_received_zip_refs_are_actual_review_basis"] is False
    assert material["local_received_zip_refs_used_to_rewrite_current_actual_review_basis"] is False
    assert material["pmn_op23_promotion_claim_refs"] == []
    assert tuple(material["implemented_steps"]) == dmh.P7_R54_AHR_POST_PMN23_DMH_OP01_IMPLEMENTED_STEPS
    assert tuple(material["not_yet_implemented_steps"]) == dmh.P7_R54_AHR_POST_PMN23_DMH_OP01_NOT_YET_IMPLEMENTED_STEPS
    assert material["next_required_step"] == dmh.P7_R54_AHR_POST_PMN23_DMH_OP02_STEP_REF
    _assert_bodyfree_no_touch_no_promotion(material)


def test_dmh_op01_blocks_if_pmn_op23_next_required_step_is_not_downstream_hold() -> None:
    pmn_op23 = _ready_pmn_op23()
    pmn_op23["next_required_step"] = "p8_start_not_allowed_bad_mutation"

    material = dmh.build_p7_r54_ahr_post_pmn23_dmh_op01_pmn_op23_downstream_manual_decision_hold_intake(
        scope_no_touch_no_promotion_refreeze=_ready_op00(),
        pmn_op23_acceptance_fail_closed_finalizer=pmn_op23,
        pmn_op23_result_memo_current_status=_status_envelope(),
    )

    assert material["dmh_op01_ready"] is False
    assert "dmh_op01_pmn_op23_acceptance_finalizer_contract_invalid" in material["dmh_op01_blocker_refs"]
    assert "dmh_op01_pmn_op23_next_required_step_mismatch" in material["dmh_op01_blocker_refs"]
    assert material["next_required_step"] == dmh.P7_R54_AHR_POST_PMN23_DMH_OP01_BLOCKED_NEXT_REQUIRED_STEP_REF
    assert dmh.assert_p7_r54_ahr_post_pmn23_dmh_op01_pmn_op23_downstream_manual_decision_hold_intake_contract(material) is True


def test_dmh_op01_blocks_if_result_memo_claims_real_review_evidence_complete() -> None:
    status = _status_envelope()
    status["actual_review_evidence_complete_from_real_review_current_status"] = True

    material = dmh.build_p7_r54_ahr_post_pmn23_dmh_op01_pmn_op23_downstream_manual_decision_hold_intake(
        scope_no_touch_no_promotion_refreeze=_ready_op00(),
        pmn_op23_acceptance_fail_closed_finalizer=_ready_pmn_op23(),
        pmn_op23_result_memo_current_status=status,
    )

    assert material["dmh_op01_ready"] is False
    assert "dmh_op01_actual_review_evidence_complete_from_real_review_current_status_not_false" in material["dmh_op01_blocker_refs"]
    assert material["actual_review_evidence_complete_from_real_review_false_confirmed"] is False
    assert material["dmh_op01_passes_to_existing_pmn_postcr22_ex_reuse_decision"] is False
    assert dmh.assert_p7_r54_ahr_post_pmn23_dmh_op01_pmn_op23_downstream_manual_decision_hold_intake_contract(material) is True


@pytest.mark.parametrize(
    ("field", "bad_value"),
    [
        ("dmh_op01_ready", False),
        ("pmn_op23_contract_fixture_complete_flag_not_promoted_to_actual_evidence", False),
        ("pmn_op23_green_is_not_actual_human_review_complete", False),
        ("dmh_op01_does_not_treat_pmn_op23_green_as_real_review_complete", False),
        ("actual_review_evidence_status_ref", "actual_review_evidence_complete_bad"),
        ("actual_review_evidence_complete_from_real_review_current_status", True),
        ("actual_review_evidence_complete_from_real_operation_claimed", True),
        ("actual_body_full_packet_generation_status_ref", "run_bad"),
        ("p8_start_allowed", True),
        ("release_allowed", True),
    ],
)
def test_dmh_op01_contract_rejects_ready_condition_real_review_or_promotion_mutation(field: str, bad_value: object) -> None:
    material = _ready_op01()
    mutated = deepcopy(material)
    mutated[field] = bad_value

    with pytest.raises(ValueError):
        dmh.assert_p7_r54_ahr_post_pmn23_dmh_op01_pmn_op23_downstream_manual_decision_hold_intake_contract(mutated)


def test_dmh_op00_op01_aliases_match_primary_builders_and_contracts() -> None:
    op00 = _ready_op00()
    alias_op00 = dmh.build_p7_r54_ahr_post_pmn23_downstream_manual_decision_hold_scope_no_touch_no_promotion_refreeze_bodyfree()
    assert alias_op00 == op00
    assert dmh.assert_p7_r54_ahr_post_pmn23_downstream_manual_decision_hold_scope_no_touch_no_promotion_refreeze_bodyfree_contract(alias_op00) is True

    primary_op01 = _ready_op01()
    alias_op01 = dmh.build_p7_r54_ahr_post_pmn23_downstream_manual_decision_hold_intake_bodyfree(
        scope_no_touch_no_promotion_refreeze=op00,
        pmn_op23_acceptance_fail_closed_finalizer=_ready_pmn_op23(),
        pmn_op23_result_memo_current_status=_status_envelope(),
    )
    assert alias_op01 == primary_op01
    assert dmh.assert_p7_r54_ahr_post_pmn23_downstream_manual_decision_hold_intake_bodyfree_contract(alias_op01) is True
