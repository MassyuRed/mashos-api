# -*- coding: utf-8 -*-
"""R54-AHR-02/03 body-free intake contract tests."""

from __future__ import annotations

from copy import deepcopy

import pytest

import emlis_ai_p7_r52_r51_handoff_p6_p8_start_decision_gate as r52
import emlis_ai_p7_r54_actual_human_review_execution_bodyfree_intake_20260627 as ahr
import emlis_ai_p7_r54_actual_local_review_operation_reentry_20260625 as r54op
import emlis_ai_p7_r54_actual_review_execution_evidence_materialization_20260626 as r54ev
import emlis_ai_p7_r54_current_snapshot_local_review_run_20260627 as r54clr
import emlis_ai_p7_r54_p5_human_blind_qa_actual_local_review_result_handoff as r54handoff
import emlis_ai_p7_r55_r54_evidence_reconcile_r52_reintake_decision_materialization as r55


def _assert_bodyfree_no_touch(material: dict[str, object]) -> None:
    assert material["body_free"] is True
    for key in ahr.P7_R54_AHR_FALSE_FLAG_REFS:
        assert material[key] is False, key
    for flag_map_key in ("public_contract", "r54_ahr_no_touch_contract", "body_free_markers"):
        assert material[flag_map_key]
        assert all(value is False for value in material[flag_map_key].values()), flag_map_key
    for forbidden_key in (
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
    ):
        assert forbidden_key not in material


def test_r54_ahr02_reconciles_historical_helper_refs_as_structural_only() -> None:
    ahr01 = ahr.build_p7_r54_ahr01_current_execution_basis_refreeze()
    material = ahr.build_p7_r54_ahr02_historical_helper_refs_reconcile(current_execution_basis_refreeze=ahr01)

    assert set(material) == set(ahr.P7_R54_AHR_HISTORICAL_HELPER_REFS_RECONCILE_REQUIRED_FIELD_REFS)
    assert material["schema_version"] == ahr.P7_R54_AHR_HISTORICAL_HELPER_REFS_RECONCILE_SCHEMA_VERSION
    assert material["policy_section"] == ahr.P7_R54_AHR02_STEP_REF
    assert material["operation_step_ref"] == ahr.P7_R54_AHR02_STEP_REF
    assert material["ahr01_schema_version"] == ahr.P7_R54_AHR_CURRENT_EXECUTION_BASIS_REFREEZE_SCHEMA_VERSION
    assert material["ahr01_next_required_step"] == ahr.P7_R54_AHR02_STEP_REF
    assert material["historical_helper_refs_reconcile_status_ref"] == ahr.P7_R54_AHR_HISTORICAL_HELPER_REFS_RECONCILE_STATUS_REF
    assert material["historical_helper_refs_reconciled"] is True
    assert material["current_execution_basis_refs"] == ahr.P7_R54_AHR_CURRENT_EXECUTION_BASIS_REFS
    assert material["current_execution_basis_refs_are_actual_execution_basis"] is True
    assert material["current_execution_basis_refs_used_as_actual_execution_basis"] is True
    assert material["operation_current_refs_match_current_execution_basis_260_83_256_169"] is True
    assert material["current_execution_basis_refs_match_received_snapshot_260_83_256_169"] is True
    assert material["current_execution_basis_refs_match_260_83_256_169_snapshot"] is True

    assert tuple(material["historical_helper_ref_groups"]) == ahr.P7_R54_AHR_HISTORICAL_HELPER_REF_GROUP_REFS
    assert material["historical_helper_ref_group_count"] == len(ahr.P7_R54_AHR_HISTORICAL_HELPER_REF_GROUP_REFS)
    assert material["historical_helper_refs"] == ahr.P7_R54_AHR_HISTORICAL_HELPER_REFS
    assert material["historical_helper_refs"]["r52_20260621"] == r52.P7_R52_CURRENT_RECEIVED_SNAPSHOT_REFS
    assert material["historical_helper_refs"]["r54_bodyfree_handoff_20260622"] == r54handoff.P7_R54_CURRENT_RECEIVED_SNAPSHOT_REFS
    assert material["historical_helper_refs"]["r55_20260623"] == r55.P7_R55_CURRENT_RECEIVED_SNAPSHOT_REFS
    assert material["historical_helper_refs"]["r54_op_20260625"] == r54op.P7_R54_OPERATION_CURRENT_REFS
    assert material["historical_helper_refs"]["r54_ev_20260626"] == r54ev.P7_R54_EV_CURRENT_RECEIVED_SNAPSHOT_REFS
    assert material["historical_helper_refs"]["r54_clr_20260627"] == r54clr.P7_R54_CLR_CURRENT_RECEIVED_SNAPSHOT_REFS
    assert material["historical_helper_role_refs"] == ahr.P7_R54_AHR_HISTORICAL_HELPER_ROLE_REFS
    assert material["historical_helper_classification_refs"] == ahr.P7_R54_AHR_HISTORICAL_HELPER_CLASSIFICATION_REFS

    match_map = material["historical_helper_refs_match_current_execution_basis_260_83_256_169"]
    assert set(match_map) == set(ahr.P7_R54_AHR_HISTORICAL_HELPER_REF_GROUP_REFS)
    assert all(value is False for value in match_map.values())
    differing = material["historical_helper_differing_current_execution_basis_ref_keys"]
    assert set(differing) == set(ahr.P7_R54_AHR_HISTORICAL_HELPER_REF_GROUP_REFS)
    assert material["differing_current_execution_basis_ref_group_count"] == len(ahr.P7_R54_AHR_HISTORICAL_HELPER_REF_GROUP_REFS)
    for group_ref, differing_keys in differing.items():
        assert "premise_zip_ref" in differing_keys, group_ref
        assert "backend_zip_ref" in differing_keys, group_ref
        assert differing_keys, group_ref

    rows = material["historical_helper_ref_rows"]
    assert len(rows) == len(ahr.P7_R54_AHR_HISTORICAL_HELPER_REF_GROUP_REFS)
    for row in rows:
        assert row["group_ref"] in ahr.P7_R54_AHR_HISTORICAL_HELPER_REF_GROUP_REFS
        assert row["classification_ref"] == "historical_structural_contract_ref_only"
        assert row["used_as_actual_execution_basis"] is False
        assert row["helper_green_can_complete_actual_review"] is False
        assert row["rewritten_here"] is False
        assert row["body_free"] is True

    assert material["r52_refs_reconciled_as_actual_evidence_decision_gate"] is True
    assert material["r54_bodyfree_handoff_refs_reconciled_as_bodyfree_handoff_contract"] is True
    assert material["r55_refs_reconciled_as_evidence_missing_hold_contract"] is True
    assert material["r54_op_refs_reconciled_as_operation_structural_helper"] is True
    assert material["r54_ev_refs_reconciled_as_evidence_materialization_structural_helper"] is True
    assert material["r54_clr_refs_reconciled_as_current_snapshot_local_run_structural_helper"] is True
    assert material["historical_helper_refs_are_historical_here"] is True
    assert material["historical_helper_refs_are_structural_refs_only"] is True
    assert material["historical_helper_refs_are_contract_refs_only"] is True
    assert material["historical_helper_refs_can_be_used_for_helper_regression_only"] is True
    assert material["historical_helper_refs_can_be_used_for_actual_execution_basis"] is False
    assert material["historical_helper_refs_used_as_actual_execution_basis"] is False
    assert material["r54_clr_historical_refs_used_as_actual_execution_basis"] is False
    assert material["old_helper_refs_allowed_as_actual_execution_basis"] is False
    assert material["r54_clr_current_refs_are_historical_here"] is True
    assert material["r54_clr_current_refs_preserved_as_historical"] is True
    assert material["r54_clr_current_refs_not_rewritten"] is True
    assert material["r54_clr_current_refs_match_current_execution_basis_260_83_256_169"] is False
    assert tuple(material["historical_helper_green_claim_boundary_refs"]) == ahr.P7_R54_AHR_PRIOR_HELPER_GREEN_CLAIM_BOUNDARY_REFS
    assert material["helper_green_not_actual_human_review_complete"] is True
    assert material["synthetic_contract_rows_not_actual_review_rows"] is True
    assert material["r52_handoff_ready_contract_not_actual_r52_reintake_execution"] is True
    assert material["reconcile_does_not_modify_helper_modules"] is True
    assert material["existing_helper_constants_not_rewritten"] is True
    assert material["existing_helper_constants_rewritten"] is False
    assert material["existing_helper_refs_preserved_as_received"] is True
    assert material["current_refs_override_uses_thin_ahr_boundary_layer"] is True
    assert material["new_thin_boundary_helper_only"] is True
    assert material["new_full_operation_helper_required_here"] is False

    assert material["body_full_generation_blocked_until_later_preflight"] is True
    assert material["body_full_generation_requested_here"] is False
    assert material["actual_human_review_completion_claim_blocked_here"] is True
    assert material["actual_rating_or_question_rows_claim_blocked_here"] is True
    assert material["disposal_receipt_claim_blocked_here"] is True
    assert material["r52_reintake_claim_blocked_here"] is True
    assert material["p6_p8_release_promotion_blocked_here"] is True
    assert material["p5_finalization_blocked_here"] is True
    assert tuple(material["implemented_steps"]) == ahr.P7_R54_AHR02_IMPLEMENTED_STEPS
    assert tuple(material["not_yet_implemented_steps"]) == ahr.P7_R54_AHR02_NOT_YET_IMPLEMENTED_STEPS
    assert material["next_required_step"] == ahr.P7_R54_AHR03_STEP_REF
    _assert_bodyfree_no_touch(material)
    assert ahr.assert_p7_r54_ahr02_historical_helper_refs_reconcile_contract(material) is True


def test_r54_ahr03_intakes_r55_hold_as_evidence_missing_before_actual_review() -> None:
    ahr02 = ahr.build_p7_r54_ahr02_historical_helper_refs_reconcile()
    material = ahr.build_p7_r54_ahr03_r55_hold_evidence_missing_intake(historical_helper_refs_reconcile=ahr02)

    assert set(material) == set(ahr.P7_R54_AHR_R55_HOLD_EVIDENCE_MISSING_INTAKE_REQUIRED_FIELD_REFS)
    assert material["schema_version"] == ahr.P7_R54_AHR_R55_HOLD_EVIDENCE_MISSING_INTAKE_SCHEMA_VERSION
    assert material["policy_section"] == ahr.P7_R54_AHR03_STEP_REF
    assert material["operation_step_ref"] == ahr.P7_R54_AHR03_STEP_REF
    assert material["ahr02_schema_version"] == ahr.P7_R54_AHR_HISTORICAL_HELPER_REFS_RECONCILE_SCHEMA_VERSION
    assert material["ahr02_next_required_step"] == ahr.P7_R54_AHR03_STEP_REF
    assert material["ahr02_historical_helper_refs_reconciled"] is True
    assert material["current_execution_basis_refs"] == ahr.P7_R54_AHR_CURRENT_EXECUTION_BASIS_REFS
    assert material["current_execution_basis_refs_are_actual_execution_basis"] is True
    assert material["current_execution_basis_refs_used_as_actual_execution_basis"] is True

    assert material["r55_hold_intake_status_ref"] == ahr.P7_R54_AHR_R55_HOLD_EVIDENCE_MISSING_STATUS_REF
    assert material["r55_hold_intaken"] is True
    assert material["r55_actual_review_evidence_gap_assessment_schema_version"] == r55.P7_R55_ACTUAL_REVIEW_EVIDENCE_GAP_ASSESSMENT_SCHEMA_VERSION
    assert material["r55_r52_reintake_decision_materialization_schema_version"] == r55.P7_R55_R52_REINTAKE_DECISION_MATERIALIZATION_SCHEMA_VERSION
    assert material["r55_gap_assessment_intaken"] is True
    assert material["r55_decision_materialization_intaken"] is True
    assert material["r55_gap_status_ref"] == ahr.P7_R54_AHR_R55_GAP_STATUS_REF
    assert material["actual_review_evidence_gap_status_ref"] == ahr.P7_R54_AHR_R55_GAP_STATUS_REF
    assert material["actual_review_evidence_missing_confirmed"] is True
    assert material["r54_handoff_status_ref"] == ahr.P7_R54_AHR_R54_R52_REINTAKE_HANDOFF_STATUS_BEFORE_RUN_REF
    assert material["r54_review_operation_state_ref"] == r55.P7_R55_R54_DEFAULT_REVIEW_OPERATION_STATE_REF
    assert material["p5_decision_before_run"] == ahr.P7_R54_AHR_P5_DECISION_BEFORE_RUN_REF
    assert material["p5_decision_status_ref"] == r55.P7_R55_P5_DECISION_STATUS_NOT_REVIEWED_REF
    assert material["r52_reintake_status_before_run"] == ahr.P7_R54_AHR_R52_REINTAKE_STATUS_BEFORE_RUN_REF
    assert material["r55_decision_ref"] == r55.P7_R55_DEFAULT_R52_REINTAKE_DECISION_REF
    assert material["r52_existing_decision_equivalent"] == r55.P7_R55_DEFAULT_R52_EXISTING_DECISION_EQUIVALENT_REF
    assert material["decision_status"] == r55.P7_R55_DEFAULT_DECISION_STATUS_REF
    assert tuple(material["decision_reason_refs"]) == r55.P7_R55_DEFAULT_DECISION_REASON_REFS
    assert material["decision_reason_ref_count"] == len(r55.P7_R55_DEFAULT_DECISION_REASON_REFS)
    assert material["r55_next_required_step"] == r55.P7_R55_R52_REINTAKE_NEXT_REQUIRED_STEP_REF

    assert material["required_case_count"] == ahr.P7_R54_AHR_R55_REQUIRED_ACTUAL_REVIEW_CASE_COUNT
    assert material["reviewed_case_count"] == 0
    assert material["sanitized_review_result_row_count"] == 0
    assert material["rating_row_count"] == 0
    assert material["question_observation_row_count"] == 0
    assert tuple(material["missing_evidence_refs"]) == ahr.P7_R54_AHR_R55_MISSING_EVIDENCE_REFS
    assert material["missing_evidence_ref_count"] == len(ahr.P7_R54_AHR_R55_MISSING_EVIDENCE_REFS)
    assert material["r55_missing_evidence_refs_match_default"] is True
    assert material["actual_rating_rows_missing"] is True
    assert material["actual_question_observation_rows_missing"] is True
    assert material["actual_disposal_receipt_missing"] is True
    assert material["actual_r52_reintake_blocked_before_run"] is True
    assert material["r52_handoff_ready_before_actual_review"] is False
    assert material["r52_reintake_ready_before_actual_review"] is False
    assert material["p5_confirmed_candidate_before_actual_review"] is False
    assert material["p8_material_candidate_before_actual_review"] is False
    assert material["next_required_step_is_local_only_preflight"] is True
    assert material["body_full_generation_blocked_until_later_preflight"] is True
    assert material["body_full_generation_requested_here"] is False
    assert material["human_review_completion_claim_blocked_here"] is True
    assert material["actual_review_completion_claim_blocked_here"] is True
    assert material["actual_human_review_completion_claim_blocked_here"] is True
    assert material["actual_rating_or_question_rows_claim_blocked_here"] is True
    assert material["disposal_receipt_claim_blocked_here"] is True
    assert material["r52_reintake_claim_blocked_here"] is True
    assert material["p6_p8_release_promotion_blocked_here"] is True
    assert material["p5_finalization_blocked_here"] is True
    assert tuple(material["implemented_steps"]) == ahr.P7_R54_AHR03_IMPLEMENTED_STEPS
    assert tuple(material["not_yet_implemented_steps"]) == ahr.P7_R54_AHR03_NOT_YET_IMPLEMENTED_STEPS
    assert material["next_required_step"] == ahr.P7_R54_AHR04_STEP_REF
    _assert_bodyfree_no_touch(material)
    assert ahr.assert_p7_r54_ahr03_r55_hold_evidence_missing_intake_contract(material) is True


@pytest.mark.parametrize(
    "key,value",
    [
        ("historical_helper_refs_can_be_used_for_actual_execution_basis", True),
        ("historical_helper_refs_used_as_actual_execution_basis", True),
        ("r54_clr_historical_refs_used_as_actual_execution_basis", True),
        ("old_helper_refs_allowed_as_actual_execution_basis", True),
        ("r54_clr_current_refs_not_rewritten", False),
        ("helper_green_not_actual_human_review_complete", False),
        ("synthetic_contract_rows_not_actual_review_rows", False),
        ("r52_handoff_ready_contract_not_actual_r52_reintake_execution", False),
        ("reconcile_does_not_modify_helper_modules", False),
        ("existing_helper_constants_not_rewritten", False),
        ("existing_helper_constants_rewritten", True),
        ("current_refs_override_uses_thin_ahr_boundary_layer", False),
        ("new_thin_boundary_helper_only", False),
        ("new_full_operation_helper_required_here", True),
        ("body_full_generation_requested_here", True),
        ("actual_human_review_executed_by_person", True),
        ("p8_start_allowed", True),
        ("release_allowed", True),
        ("raw_body_included", True),
        ("question_text_included", True),
    ],
)
def test_r54_ahr02_rejects_helper_reconcile_boundary_mutations(key: str, value: object) -> None:
    mutated = deepcopy(ahr.build_p7_r54_ahr02_historical_helper_refs_reconcile())
    mutated[key] = value
    with pytest.raises(ValueError):
        ahr.assert_p7_r54_ahr02_historical_helper_refs_reconcile_contract(mutated)


@pytest.mark.parametrize(
    "key,value",
    [
        ("r55_gap_status_ref", "OTHER"),
        ("actual_review_evidence_gap_status_ref", "OTHER"),
        ("actual_review_evidence_missing_confirmed", False),
        ("r52_reintake_status_before_run", "READY"),
        ("reviewed_case_count", 24),
        ("sanitized_review_result_row_count", 24),
        ("rating_row_count", 24),
        ("question_observation_row_count", 24),
        ("actual_rating_rows_missing", False),
        ("actual_question_observation_rows_missing", False),
        ("actual_disposal_receipt_missing", False),
        ("actual_r52_reintake_blocked_before_run", False),
        ("r52_handoff_ready_before_actual_review", True),
        ("r52_reintake_ready_before_actual_review", True),
        ("p5_confirmed_candidate_before_actual_review", True),
        ("p8_material_candidate_before_actual_review", True),
        ("next_required_step_is_local_only_preflight", False),
        ("body_full_generation_requested_here", True),
        ("actual_human_review_executed_by_person", True),
        ("disposal_verified", True),
        ("p5_final_allowed", True),
        ("p6_start_allowed", True),
        ("p8_start_allowed", True),
        ("release_allowed", True),
        ("question_text_included", True),
    ],
)
def test_r54_ahr03_rejects_evidence_missing_or_promotion_mutations(key: str, value: object) -> None:
    mutated = deepcopy(ahr.build_p7_r54_ahr03_r55_hold_evidence_missing_intake())
    mutated[key] = value
    with pytest.raises(ValueError):
        ahr.assert_p7_r54_ahr03_r55_hold_evidence_missing_intake_contract(mutated)


def test_r54_ahr03_rejects_passing_ahr02_that_does_not_reconcile_historical_refs() -> None:
    broken_ahr02 = deepcopy(ahr.build_p7_r54_ahr02_historical_helper_refs_reconcile())
    broken_ahr02["helper_green_not_actual_human_review_complete"] = False
    with pytest.raises(ValueError):
        ahr.build_p7_r54_ahr03_r55_hold_evidence_missing_intake(historical_helper_refs_reconcile=broken_ahr02)
