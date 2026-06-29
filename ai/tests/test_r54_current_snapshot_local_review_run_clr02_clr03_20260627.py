# -*- coding: utf-8 -*-
"""R54 current snapshot local review run CLR02-CLR03 contract tests."""

from __future__ import annotations

from copy import deepcopy
from typing import Any

import pytest

import emlis_ai_p7_r52_r51_handoff_p6_p8_start_decision_gate as r52
import emlis_ai_p7_r53_r51_actual_local_review_execution_evidence_materialization as r53
import emlis_ai_p7_r54_p5_human_blind_qa_actual_local_review_result_handoff as r54handoff
import emlis_ai_p7_r55_r54_evidence_reconcile_r52_reintake_decision_materialization as r55
import emlis_ai_product_readfeel_p4_r11_summary_decision_handoff as p4r11
import emlis_ai_p7_r54_current_snapshot_local_review_run_20260627 as clr


FORBIDDEN_BODY_OR_QUESTION_KEYS = (
    "raw_input",
    "returned_emlis_body",
    "history_surface",
    "reviewer_free_text",
    "reviewer_note",
    "reviewer_notes",
    "question_text",
    "draft_question_text",
    "local_absolute_path",
    "body_hash",
    "packet_content",
    "terminal_output_body",
)


def _assert_bodyfree_no_touch(material: dict[str, Any]) -> None:
    assert material["body_free"] is True
    for key in clr.P7_R54_CLR_FALSE_FLAG_REFS:
        assert material[key] is False, key
    for flag_map_key in ("public_contract", "r54_clr_no_touch_contract", "body_free_markers"):
        assert material[flag_map_key]
        assert all(value is False for value in material[flag_map_key].values()), flag_map_key
    for forbidden_key in FORBIDDEN_BODY_OR_QUESTION_KEYS:
        assert forbidden_key not in material


def test_r54_clr00_clr01_are_present_before_clr02_clr03() -> None:
    clr00 = clr.build_p7_r54_clr00_scope_no_touch_boundary_freeze()
    clr01 = clr.build_p7_r54_clr01_current_snapshot_basis_refreeze(scope_no_touch_boundary_freeze=clr00)

    assert clr.assert_p7_r54_clr00_scope_no_touch_boundary_freeze_contract(clr00) is True
    assert clr.assert_p7_r54_clr01_current_snapshot_basis_refreeze_contract(clr01) is True
    assert tuple(clr01["implemented_steps"]) == clr.P7_R54_CLR01_IMPLEMENTED_STEPS
    assert clr01["next_required_step"] == clr.P7_R54_CLR02_STEP_REF
    assert clr01["operation_current_refs"] == clr.P7_R54_CLR_CURRENT_RECEIVED_SNAPSHOT_REFS
    assert clr01["operation_current_refs_used_as_actual_review_basis"] is True
    assert clr01["historical_helper_refs_used_as_actual_review_basis"] is False


def test_r54_clr02_reconciles_historical_helper_refs_without_using_them_as_actual_basis() -> None:
    clr01 = clr.build_p7_r54_clr01_current_snapshot_basis_refreeze()
    material = clr.build_p7_r54_clr02_historical_helper_refs_reconcile(current_snapshot_basis_refreeze=clr01)

    assert set(material) == set(clr.P7_R54_CLR02_HISTORICAL_HELPER_REFS_RECONCILE_REQUIRED_FIELD_REFS)
    assert material["schema_version"] == clr.P7_R54_CLR_HISTORICAL_HELPER_REFS_RECONCILE_SCHEMA_VERSION
    assert material["policy_section"] == clr.P7_R54_CLR02_STEP_REF
    assert material["operation_step_ref"] == clr.P7_R54_CLR02_STEP_REF
    assert material["clr01_schema_version"] == clr.P7_R54_CLR_CURRENT_SNAPSHOT_BASIS_REFREEZE_SCHEMA_VERSION
    assert material["clr01_next_required_step"] == clr.P7_R54_CLR02_STEP_REF
    assert material["clr01_current_snapshot_basis_refrozen"] is True
    assert material["clr01_current_refs_refreeze_does_not_rewrite_historical_helpers"] is True

    assert material["historical_reconcile_status_ref"] == clr.P7_R54_CLR02_HISTORICAL_RECONCILE_STATUS_REF
    assert tuple(material["historical_helper_ref_groups"]) == clr.P7_R54_CLR02_HISTORICAL_RECONCILE_REF_GROUP_REFS
    assert material["historical_helper_ref_group_count"] == 7
    assert material["historical_ref_details"] == clr.P7_R54_CLR02_HISTORICAL_RECONCILE_REF_DETAILS
    assert material["historical_ref_detail_count"] == 7
    assert set(material["historical_ref_details"]) == {
        "r54_op_20260625",
        "r54_ev_20260626",
        "r55_20260623",
        "r52_20260621",
        "r53_20260621",
        "r54_bodyfree_handoff_20260622",
        "p4_r11_20260624",
    }
    assert material["historical_ref_details"]["r52_20260621"]["received_snapshot_refs"] == r52.P7_R52_CURRENT_RECEIVED_SNAPSHOT_REFS
    assert material["historical_ref_details"]["r53_20260621"]["received_snapshot_refs"] == r53.P7_R53_CURRENT_RECEIVED_SNAPSHOT_REFS
    assert (
        material["historical_ref_details"]["r54_bodyfree_handoff_20260622"]["received_snapshot_refs"]
        == r54handoff.P7_R54_CURRENT_RECEIVED_SNAPSHOT_REFS
    )
    assert (
        material["historical_ref_details"]["p4_r11_20260624"]["summary_schema_version_ref"]
        == p4r11.PRODUCT_READFEEL_P4_R11_SUMMARY_DECISION_HANDOFF_VERSION_20260624
    )
    assert (
        material["historical_ref_details"]["p4_r11_20260624"]["r54_return_next_step_ref"]
        == p4r11.P4_R11_NEXT_STEP_R54_ACTUAL_LOCAL_ONLY_HUMAN_REVIEW_20260624
    )
    for group_ref, details in material["historical_ref_details"].items():
        assert details["used_for_helper_regression_only"] is True, group_ref
        assert details["used_for_actual_review_basis"] is False, group_ref

    assert material["historical_helper_refs_reconciled"] is True
    assert material["historical_helper_refs_reconciled_as_bodyfree_context_only"] is True
    assert material["historical_helper_refs_are_structural_refs_only"] is True
    assert material["structural_contract_reused"] is True
    assert material["helper_regression_context_preserved"] is True
    assert material["historical_refs_can_be_used_for_helper_regression_only"] is True
    assert material["historical_refs_can_be_used_for_actual_review_basis"] is False
    assert material["historical_refs_used_as_actual_review_basis"] is False
    assert material["older_helper_refs_mixed_into_actual_review_basis"] is False
    assert material["p4_r11_audit_rows_converted_to_r54_actual_review_cases"] is False
    assert material["p4_r11_audit_rows_mixed_into_r54_review_cases"] is False
    assert material["current_snapshot_basis_preserved"] is True
    assert material["operation_current_refs_still_actual_review_basis"] is True
    assert material["operation_current_refs"] == clr.P7_R54_CLR_CURRENT_RECEIVED_SNAPSHOT_REFS
    assert material["operation_current_refs_used_as_actual_review_basis"] is True
    assert tuple(material["implemented_steps"]) == clr.P7_R54_CLR02_IMPLEMENTED_STEPS
    assert tuple(material["not_yet_implemented_steps"]) == clr.P7_R54_CLR02_NOT_YET_IMPLEMENTED_STEPS
    assert material["next_required_step"] == clr.P7_R54_CLR03_STEP_REF
    _assert_bodyfree_no_touch(material)
    assert clr.assert_p7_r54_clr02_historical_helper_refs_reconcile_contract(material) is True


def test_r54_clr03_intakes_r55_hold_and_keeps_evidence_missing_before_actual_review() -> None:
    clr02 = clr.build_p7_r54_clr02_historical_helper_refs_reconcile()
    material = clr.build_p7_r54_clr03_r55_hold_evidence_missing_intake(historical_helper_refs_reconcile=clr02)

    assert set(material) == set(clr.P7_R54_CLR03_R55_HOLD_EVIDENCE_MISSING_INTAKE_REQUIRED_FIELD_REFS)
    assert material["schema_version"] == clr.P7_R54_CLR_R55_HOLD_EVIDENCE_MISSING_INTAKE_SCHEMA_VERSION
    assert material["policy_section"] == clr.P7_R54_CLR03_STEP_REF
    assert material["operation_step_ref"] == clr.P7_R54_CLR03_STEP_REF
    assert material["clr02_schema_version"] == clr.P7_R54_CLR_HISTORICAL_HELPER_REFS_RECONCILE_SCHEMA_VERSION
    assert material["clr02_next_required_step"] == clr.P7_R54_CLR03_STEP_REF
    assert material["clr02_historical_helper_refs_reconciled"] is True

    assert material["r55_hold_intake_status_ref"] == clr.P7_R54_CLR03_R55_HOLD_EVIDENCE_MISSING_INTAKE_STATUS_REF
    assert material["r55_gap_assessment_schema_version"] == r55.P7_R55_ACTUAL_REVIEW_EVIDENCE_GAP_ASSESSMENT_SCHEMA_VERSION
    assert material["r55_r52_decision_schema_version"] == r55.P7_R55_R52_REINTAKE_DECISION_MATERIALIZATION_SCHEMA_VERSION
    assert material["r55_current_received_snapshot_refs"] == r55.P7_R55_CURRENT_RECEIVED_SNAPSHOT_REFS
    assert material["r55_actual_review_basis_ref"] == r55.P7_R55_ACTUAL_REVIEW_BASIS_REF
    assert material["r55_gap_status_ref"] == r55.P7_R55_ACTUAL_REVIEW_EVIDENCE_MISSING_GAP_STATUS_REF
    assert material["r55_p5_decision_status_ref"] == r55.P7_R55_P5_DECISION_STATUS_NOT_REVIEWED_REF
    assert material["r55_decision_ref"] == r55.P7_R55_DEFAULT_R52_REINTAKE_DECISION_REF
    assert material["r55_decision_status"] == r55.P7_R55_DEFAULT_DECISION_STATUS_REF
    assert material["r55_next_required_step"] == r55.P7_R55_R52_REINTAKE_NEXT_REQUIRED_STEP_REF
    assert material["r55_handoff_status_ref"] == r55.P7_R55_R54_DEFAULT_HANDOFF_EXPECTED_STATUS_REF
    assert material["r55_review_operation_state_ref"] == r55.P7_R55_R54_DEFAULT_REVIEW_OPERATION_STATE_REF
    assert material["r55_hold_state_preserved"] is True
    assert material["r55_hold_is_current_pre_run_assumption"] is True
    assert material["r55_hold_released_here"] is False
    assert material["r55_decision_reclassified_here"] is False

    assert material["required_case_count"] == 24
    assert material["reviewed_case_count_before_run"] == 0
    assert material["rating_row_count_before_run"] == 0
    assert material["question_observation_row_count_before_run"] == 0
    assert material["disposal_verified_before_run"] is False
    assert tuple(material["missing_evidence_refs"]) == r55.P7_R55_DEFAULT_MISSING_EVIDENCE_REFS
    assert material["missing_evidence_ref_count"] == len(r55.P7_R55_DEFAULT_MISSING_EVIDENCE_REFS)
    assert material["actual_review_evidence_missing_before_run"] is True
    assert material["actual_review_evidence_complete_before_run"] is False
    assert material["actual_human_review_run_before_clr03"] is False
    assert material["actual_rating_rows_materialized_before_run"] is False
    assert material["actual_question_need_observation_rows_materialized_before_run"] is False
    assert material["actual_disposal_receipt_materialized_before_run"] is False
    assert material["r52_reintake_blocked_by_actual_review_evidence_missing"] is True
    assert material["r52_reintake_handoff_status_ref"] == clr.P7_R54_CLR03_R52_REINTAKE_BLOCKED_STATUS_REF
    assert material["p5_decision_candidate_before_run_ref"] == clr.P7_R54_CLR03_P5_DECISION_CANDIDATE_BEFORE_RUN_REF
    assert material["p5_human_blind_qa_confirmed_final_before_run"] is False
    assert material["p6_hold"] is True
    assert material["p8_hold"] is True
    assert material["release_hold"] is True
    assert material["p6_limited_human_readfeel_start_allowed_before_run"] is False
    assert material["p8_start_allowed_before_run"] is False
    assert material["release_allowed_before_run"] is False
    assert material["evidence_missing_classified_as_p5_repair_required"] is False
    assert material["evidence_missing_classified_as_p8_material_candidate"] is False
    assert material["operation_current_refs"] == clr.P7_R54_CLR_CURRENT_RECEIVED_SNAPSHOT_REFS
    assert material["operation_current_refs_used_as_actual_review_basis"] is True
    assert tuple(material["implemented_steps"]) == clr.P7_R54_CLR03_IMPLEMENTED_STEPS
    assert tuple(material["not_yet_implemented_steps"]) == clr.P7_R54_CLR03_NOT_YET_IMPLEMENTED_STEPS
    assert material["next_required_step"] == clr.P7_R54_CLR04_STEP_REF
    _assert_bodyfree_no_touch(material)
    assert clr.assert_p7_r54_clr03_r55_hold_evidence_missing_intake_contract(material) is True


@pytest.mark.parametrize(
    "key,value",
    [
        ("historical_refs_can_be_used_for_actual_review_basis", True),
        ("historical_refs_used_as_actual_review_basis", True),
        ("older_helper_refs_mixed_into_actual_review_basis", True),
        ("p4_r11_audit_rows_converted_to_r54_actual_review_cases", True),
        ("p4_r11_audit_rows_mixed_into_r54_review_cases", True),
        ("current_snapshot_basis_preserved", False),
        ("operation_current_refs_still_actual_review_basis", False),
        ("historical_helper_current_refs_preserved", False),
        ("existing_helper_constants_not_rewritten", False),
        ("existing_helper_constants_rewritten", True),
        ("body_full_packet_generated_here", True),
        ("actual_human_review_run_here", True),
        ("p8_start_allowed", True),
        ("release_allowed", True),
    ],
)
def test_r54_clr02_rejects_basis_mixing_or_promotion_mutations(key: str, value: object) -> None:
    material = clr.build_p7_r54_clr02_historical_helper_refs_reconcile()
    mutated = deepcopy(material)
    mutated[key] = value
    with pytest.raises(ValueError):
        clr.assert_p7_r54_clr02_historical_helper_refs_reconcile_contract(mutated)


@pytest.mark.parametrize(
    "key,value",
    [
        ("r55_gap_status_ref", "ACTUAL_REVIEW_EVIDENCE_COMPLETE"),
        ("r55_hold_released_here", True),
        ("r55_decision_reclassified_here", True),
        ("reviewed_case_count_before_run", 24),
        ("rating_row_count_before_run", 24),
        ("question_observation_row_count_before_run", 24),
        ("disposal_verified_before_run", True),
        ("actual_review_evidence_missing_before_run", False),
        ("actual_review_evidence_complete_before_run", True),
        ("actual_human_review_run_before_clr03", True),
        ("actual_rating_rows_materialized_before_run", True),
        ("actual_question_need_observation_rows_materialized_before_run", True),
        ("actual_disposal_receipt_materialized_before_run", True),
        ("r52_reintake_blocked_by_actual_review_evidence_missing", False),
        ("p6_hold", False),
        ("p8_hold", False),
        ("release_hold", False),
        ("p6_limited_human_readfeel_start_allowed_before_run", True),
        ("p8_start_allowed_before_run", True),
        ("release_allowed_before_run", True),
        ("evidence_missing_classified_as_p5_repair_required", True),
        ("evidence_missing_classified_as_p8_material_candidate", True),
        ("p8_start_allowed", True),
        ("release_allowed", True),
    ],
)
def test_r54_clr03_rejects_hold_release_evidence_claim_or_promotion_mutations(key: str, value: object) -> None:
    material = clr.build_p7_r54_clr03_r55_hold_evidence_missing_intake()
    mutated = deepcopy(material)
    mutated[key] = value
    with pytest.raises(ValueError):
        clr.assert_p7_r54_clr03_r55_hold_evidence_missing_intake_contract(mutated)


def test_r54_clr02_clr03_reject_body_or_question_payload_keys() -> None:
    clr02 = clr.build_p7_r54_clr02_historical_helper_refs_reconcile()
    mutated02 = deepcopy(clr02)
    mutated02["question_text"] = "forbidden"
    with pytest.raises(ValueError):
        clr.assert_p7_r54_clr02_historical_helper_refs_reconcile_contract(mutated02)

    clr03 = clr.build_p7_r54_clr03_r55_hold_evidence_missing_intake()
    mutated03 = deepcopy(clr03)
    mutated03["raw_input"] = "forbidden"
    with pytest.raises(ValueError):
        clr.assert_p7_r54_clr03_r55_hold_evidence_missing_intake_contract(mutated03)


def test_r54_clr02_clr03_aliases_preserve_contract() -> None:
    clr02 = clr.build_p7_r54_current_snapshot_historical_helper_refs_reconcile_bodyfree()
    assert clr.assert_p7_r54_current_snapshot_historical_helper_refs_reconcile_bodyfree_contract(clr02) is True
    assert clr.assert_p7_r54_current_snapshot_local_run_clr02_historical_helper_refs_reconcile_contract(clr02) is True

    clr03 = clr.build_p7_r54_current_snapshot_r55_hold_evidence_missing_intake_bodyfree(
        historical_helper_refs_reconcile=clr02
    )
    assert clr.assert_p7_r54_current_snapshot_r55_hold_evidence_missing_intake_bodyfree_contract(clr03) is True
    assert clr.assert_p7_r54_current_snapshot_local_run_clr03_r55_hold_evidence_missing_intake_contract(clr03) is True
