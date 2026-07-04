# -*- coding: utf-8 -*-
"""R54-AHR Post-DMH18 downstream manual decision triage DMD-OP02/OP03 tests."""

from __future__ import annotations

from copy import deepcopy
from pathlib import Path
import sys

import pytest

TEST_DIR = Path(__file__).resolve().parent
if str(TEST_DIR) not in sys.path:
    sys.path.insert(0, str(TEST_DIR))

import emlis_ai_p7_r54_ahr_post_dmh18_downstream_manual_decision_triage_20260703 as dmd
import emlis_ai_p7_r54_ahr_post_pmn23_downstream_manual_decision_hold_evidence_intake_20260701 as dmh

_READY_OP18_CACHE: dict[str, object] | None = None


def _blocked_op18() -> dict[str, object]:
    material = dmh.build_p7_r54_ahr_post_pmn23_dmh_op18_result_memo_downstream_manual_decision_hold_finalizer()
    assert material["dmh_op18_status_ref"] == dmh.P7_R54_AHR_POST_PMN23_DMH_OP18_BLOCKED_STATUS_REF
    assert dmh.assert_p7_r54_ahr_post_pmn23_dmh_op18_result_memo_downstream_manual_decision_hold_finalizer_contract(material) is True
    return material


def _ready_op18() -> dict[str, object]:
    global _READY_OP18_CACHE
    if _READY_OP18_CACHE is None:
        material = _blocked_op18()
        material.update(
            {
                "op17_schema_version": "op17_schema_contract_valid_fixture",
                "op17_material_ref": "op17_contract_valid_ready_fixture",
                "op17_next_required_step": dmh.P7_R54_AHR_POST_PMN23_DMH_OP18_STEP_REF,
                "op17_dmh_ready": True,
                "op17_postcr22_ex07_ex18_reentry_envelope_ready": True,
                "op17_actual_review_evidence_complete_from_real_review": True,
                "op17_actual_review_evidence_complete_predicate_carried_into_reentry_envelope": True,
                "dmh_op18_status_ref": dmh.P7_R54_AHR_POST_PMN23_DMH_OP18_READY_STATUS_REF,
                "dmh_op18_ready": True,
                "dmh_op18_reason_refs": list(dmh.P7_R54_AHR_POST_PMN23_DMH_OP18_READY_REASON_REFS),
                "dmh_op18_reason_ref_count": len(dmh.P7_R54_AHR_POST_PMN23_DMH_OP18_READY_REASON_REFS),
                "dmh_op18_blocker_refs": [],
                "dmh_op18_blocker_ref_count": 0,
                "result_memo_bodyfree_closed": True,
                "downstream_manual_decision_hold_state_ref": dmh.P7_R54_AHR_POST_PMN23_DMH_OP18_DOWNSTREAM_MANUAL_DECISION_HOLD_STATE_REF,
                "downstream_manual_decision_hold_finalized": True,
                "manual_downstream_decision_required": True,
                "actual_review_evidence_complete_candidate_from_real_review": True,
                "actual_review_evidence_complete_from_real_review": True,
                "actual_review_evidence_complete_predicate_carried_into_reentry_envelope": True,
                "evidence_completion_state_ref": dmh.P7_R54_AHR_POST_PMN23_DMH_OP18_EVIDENCE_COMPLETE_STATE_REF,
                "evidence_incomplete_continue_or_retry_required": False,
                "bodyfree_evidence_boundary_repair_required": False,
                "postcr22_ex07_ex18_reentry_ready_candidate": True,
                "implemented_steps": list(dmh.P7_R54_AHR_POST_PMN23_DMH_OP18_IMPLEMENTED_STEPS),
                "not_yet_implemented_steps": list(dmh.P7_R54_AHR_POST_PMN23_DMH_OP18_NOT_YET_IMPLEMENTED_STEPS),
                "next_required_step": dmh.P7_R54_AHR_POST_PMN23_DMH_OP18_NEXT_REQUIRED_STEP_EVIDENCE_COMPLETE_REF,
            }
        )
        assert dmh.assert_p7_r54_ahr_post_pmn23_dmh_op18_result_memo_downstream_manual_decision_hold_finalizer_contract(material) is True
        _READY_OP18_CACHE = material
    return deepcopy(_READY_OP18_CACHE)


def _op01_ready() -> dict[str, object]:
    material = dmd.build_p7_r54_ahr_post_dmh18_dmd_op01_op18_finalizer_bodyfree_intake(
        op18_result_memo_downstream_manual_decision_hold_finalizer=_ready_op18(),
    )
    assert dmd.assert_p7_r54_ahr_post_dmh18_dmd_op01_op18_finalizer_bodyfree_intake_contract(material) is True
    return material


def _valid_receipt() -> dict[str, object]:
    return {
        "schema_version": dmd.P7_R54_AHR_POST_DMH18_DMD_ACTUAL_OPERATION_EVIDENCE_RECEIPT_SCHEMA_VERSION,
        "operation_receipt_ref": "dmd_op02_op03_actual_operation_receipt_bodyfree_fixture_001",
        "review_session_id": dmd.P7_R54_AHR_POST_DMH18_DMD_DEFAULT_REVIEW_SESSION_ID,
        "source_kind_ref": dmd.P7_R54_AHR_POST_DMH18_DMD_ACTUAL_OPERATION_SOURCE_KIND_REF,
        "created_from_real_operation": True,
        "actual_source_guard_passed": True,
        "actual_human_review_executed_by_person": True,
        "reviewed_case_count": dmd.P7_R54_AHR_POST_DMH18_DMD_REQUIRED_EVIDENCE_COUNT,
        "selection_row_count": dmd.P7_R54_AHR_POST_DMH18_DMD_REQUIRED_EVIDENCE_COUNT,
        "sanitized_review_result_row_count": dmd.P7_R54_AHR_POST_DMH18_DMD_REQUIRED_EVIDENCE_COUNT,
        "rating_row_count": dmd.P7_R54_AHR_POST_DMH18_DMD_REQUIRED_EVIDENCE_COUNT,
        "question_need_observation_row_count": dmd.P7_R54_AHR_POST_DMH18_DMD_REQUIRED_EVIDENCE_COUNT,
        "disposal_purge_receipt_accepted": True,
        "no_body_leak_validation_passed": True,
        "no_question_text_validation_passed": True,
        "no_path_hash_validation_passed": True,
        "no_terminal_output_body_validation_passed": True,
        "no_touch_validation_passed": True,
        "body_free": True,
    }


def _assert_common_bodyfree_no_touch_no_promotion(material: dict[str, object]) -> None:
    assert material["body_free"] is True
    assert material["git_connection_required"] is False
    assert material["git_checked"] is False
    for field in dmd.P7_R54_AHR_POST_DMH18_DMD_REQUIRED_FALSE_FLAG_REFS:
        assert material[field] is False, field
    for marker_map_key in ("public_contract", "post_dmh18_no_touch_contract", "body_free_markers"):
        assert material[marker_map_key]
        assert all(value is False for value in material[marker_map_key].values()), marker_map_key
    assert all(value is False for value in material["not_claimed_boundary"].values())


def test_dmd_op02_ready_op18_without_receipt_keeps_candidate_only_and_passes_to_op03() -> None:
    material = dmd.build_p7_r54_ahr_post_dmh18_dmd_op02_candidate_vs_real_operation_evidence_claim_separation(
        op18_finalizer_bodyfree_intake=_op01_ready(),
    )

    assert set(material) == set(dmd.P7_R54_AHR_POST_DMH18_DMD_OP02_REQUIRED_FIELD_REFS)
    assert material["schema_version"] == dmd.P7_R54_AHR_POST_DMH18_DMD_OP02_SCHEMA_VERSION
    assert material["dmd_op02_status_ref"] == dmd.P7_R54_AHR_POST_DMH18_DMD_OP02_STATUS_CANDIDATE_ONLY_REF
    assert material["candidate_supported"] is True
    assert material["external_actual_operation_evidence_receipt_present"] is False
    assert material["claimed_from_real_operation"] is False
    assert "dmd_op02_external_actual_operation_evidence_receipt_missing" in material["claimed_from_real_operation_blocker_refs"]
    assert material["op18_ready_path_not_promoted_to_real_operation_claim"] is True
    assert material["candidate_supported_not_auto_promoted_to_claimed_from_real_operation"] is True
    assert material["actual_review_evidence_complete_from_real_operation_claimed_here_by_dmd_op02"] is False
    assert material["branch_candidate_ref"] == dmd.P7_R54_AHR_POST_DMH18_DMD_BRANCH_EVIDENCE_INCOMPLETE_REF
    assert material["next_required_step"] == dmd.P7_R54_AHR_POST_DMH18_DMD_NEXT_STEP_DMD_OP03_REF
    assert tuple(material["implemented_steps"]) == dmd.P7_R54_AHR_POST_DMH18_DMD_OP02_IMPLEMENTED_STEPS
    assert dmd.assert_p7_r54_ahr_post_dmh18_dmd_op02_candidate_vs_real_operation_evidence_claim_separation_contract(material) is True
    _assert_common_bodyfree_no_touch_no_promotion(material)


def test_dmd_op03_current_ready_op18_without_receipt_inventory_is_branch_a_continue_or_retry() -> None:
    op02 = dmd.build_p7_r54_ahr_post_dmh18_dmd_op02_candidate_vs_real_operation_evidence_claim_separation(
        op18_finalizer_bodyfree_intake=_op01_ready(),
    )
    material = dmd.build_p7_r54_ahr_post_dmh18_dmd_op03_actual_evidence_receipt_completeness_inventory(
        candidate_vs_real_operation_evidence_claim_separation=op02,
    )

    assert set(material) == set(dmd.P7_R54_AHR_POST_DMH18_DMD_OP03_REQUIRED_FIELD_REFS)
    assert material["schema_version"] == dmd.P7_R54_AHR_POST_DMH18_DMD_OP03_SCHEMA_VERSION
    assert material["dmd_op03_status_ref"] == dmd.P7_R54_AHR_POST_DMH18_DMD_OP03_STATUS_MISSING_REF
    assert material["actual_evidence_status_ref"] == dmd.P7_R54_AHR_POST_DMH18_DMD_ACTUAL_EVIDENCE_STATUS_INCOMPLETE_REF
    assert material["actual_evidence_receipt_present"] is False
    assert material["actual_evidence_receipt_complete"] is False
    assert material["actual_evidence_receipt_missing_or_incomplete"] is True
    assert material["evidence_incomplete_continue_or_retry_required"] is True
    assert material["branch_candidate_ref"] == dmd.P7_R54_AHR_POST_DMH18_DMD_BRANCH_EVIDENCE_INCOMPLETE_REF
    assert material["next_required_step"] == dmd.P7_R54_AHR_POST_DMH18_DMD_NEXT_STEP_CONTINUE_OR_RETRY_ACTUAL_REVIEW_REF
    assert tuple(material["implemented_steps"]) == dmd.P7_R54_AHR_POST_DMH18_DMD_OP03_IMPLEMENTED_STEPS
    assert dmd.assert_p7_r54_ahr_post_dmh18_dmd_op03_actual_evidence_receipt_completeness_inventory_contract(material) is True
    _assert_common_bodyfree_no_touch_no_promotion(material)


def test_dmd_op02_valid_external_receipt_can_support_real_operation_claim_without_claiming_execution_here() -> None:
    material = dmd.build_p7_r54_ahr_post_dmh18_dmd_op02_candidate_vs_real_operation_evidence_claim_separation(
        op18_finalizer_bodyfree_intake=_op01_ready(),
        actual_operation_evidence_receipt_bodyfree_optional=_valid_receipt(),
    )

    assert material["dmd_op02_status_ref"] == dmd.P7_R54_AHR_POST_DMH18_DMD_OP02_STATUS_REAL_OPERATION_CLAIM_SUPPORTED_REF
    assert material["candidate_supported"] is True
    assert material["external_actual_operation_evidence_receipt_present"] is True
    assert material["external_actual_operation_evidence_receipt_source_kind_valid"] is True
    assert material["external_actual_operation_evidence_receipt_counts_and_guards_passed"] is True
    assert material["claimed_from_real_operation"] is True
    assert material["actual_review_evidence_complete_from_real_operation_claimed_here_by_dmd_op02"] is False
    assert material["branch_candidate_ref"] == dmd.P7_R54_AHR_POST_DMH18_DMD_BRANCH_EVIDENCE_COMPLETE_MANUAL_DECISION_NO_AUTO_EXEC_REF
    assert material["next_required_step"] == dmd.P7_R54_AHR_POST_DMH18_DMD_NEXT_STEP_DMD_OP03_REF
    assert dmd.assert_p7_r54_ahr_post_dmh18_dmd_op02_candidate_vs_real_operation_evidence_claim_separation_contract(material) is True
    _assert_common_bodyfree_no_touch_no_promotion(material)


def test_dmd_op03_valid_external_receipt_inventory_becomes_complete_candidate_but_only_passes_to_op04() -> None:
    receipt = _valid_receipt()
    op02 = dmd.build_p7_r54_ahr_post_dmh18_dmd_op02_candidate_vs_real_operation_evidence_claim_separation(
        op18_finalizer_bodyfree_intake=_op01_ready(),
        actual_operation_evidence_receipt_bodyfree_optional=receipt,
    )
    material = dmd.build_p7_r54_ahr_post_dmh18_dmd_op03_actual_evidence_receipt_completeness_inventory(
        candidate_vs_real_operation_evidence_claim_separation=op02,
        actual_operation_evidence_receipt_bodyfree_optional=receipt,
    )

    assert material["dmd_op03_status_ref"] == dmd.P7_R54_AHR_POST_DMH18_DMD_OP03_STATUS_COMPLETE_REF
    assert material["actual_evidence_status_ref"] == dmd.P7_R54_AHR_POST_DMH18_DMD_ACTUAL_EVIDENCE_STATUS_COMPLETE_CANDIDATE_REF
    assert material["actual_evidence_receipt_complete"] is True
    assert material["complete_candidate_for_manual_decision_branch"] is True
    assert material["downstream_manual_decision_required_without_auto_execution"] is False
    assert material["branch_candidate_ref"] == dmd.P7_R54_AHR_POST_DMH18_DMD_BRANCH_EVIDENCE_COMPLETE_MANUAL_DECISION_NO_AUTO_EXEC_REF
    assert material["next_required_step"] == dmd.P7_R54_AHR_POST_DMH18_DMD_NEXT_STEP_DMD_OP04_REF
    assert material["postcr22_ex07_ex18_reentry_executed_here"] is False
    assert material["r52_actual_execution_started_here"] is False
    assert material["p5_final_allowed"] is False
    assert material["p6_start_allowed"] is False
    assert material["p8_start_allowed"] is False
    assert material["p7_complete"] is False
    assert material["release_allowed"] is False
    assert dmd.assert_p7_r54_ahr_post_dmh18_dmd_op03_actual_evidence_receipt_completeness_inventory_contract(material) is True
    _assert_common_bodyfree_no_touch_no_promotion(material)


@pytest.mark.parametrize(
    ("count_field", "bad_value"),
    [
        ("reviewed_case_count", 23),
        ("selection_row_count", 23),
        ("sanitized_review_result_row_count", 23),
        ("rating_row_count", 23),
        ("question_need_observation_row_count", 23),
    ],
)
def test_dmd_op03_count_mismatch_stays_incomplete_not_manual_decision(count_field: str, bad_value: int) -> None:
    receipt = _valid_receipt()
    receipt[count_field] = bad_value
    op02 = dmd.build_p7_r54_ahr_post_dmh18_dmd_op02_candidate_vs_real_operation_evidence_claim_separation(
        op18_finalizer_bodyfree_intake=_op01_ready(),
        actual_operation_evidence_receipt_bodyfree_optional=receipt,
    )
    material = dmd.build_p7_r54_ahr_post_dmh18_dmd_op03_actual_evidence_receipt_completeness_inventory(
        candidate_vs_real_operation_evidence_claim_separation=op02,
        actual_operation_evidence_receipt_bodyfree_optional=receipt,
    )

    assert material["dmd_op03_status_ref"] == dmd.P7_R54_AHR_POST_DMH18_DMD_OP03_STATUS_INCOMPLETE_REF
    assert material[f"{count_field}_is_24"] is False
    assert material["actual_evidence_receipt_complete"] is False
    assert material["branch_candidate_ref"] == dmd.P7_R54_AHR_POST_DMH18_DMD_BRANCH_EVIDENCE_INCOMPLETE_REF
    assert material["next_required_step"] == dmd.P7_R54_AHR_POST_DMH18_DMD_NEXT_STEP_CONTINUE_OR_RETRY_ACTUAL_REVIEW_REF
    assert dmd.assert_p7_r54_ahr_post_dmh18_dmd_op03_actual_evidence_receipt_completeness_inventory_contract(material) is True
    _assert_common_bodyfree_no_touch_no_promotion(material)


def test_dmd_op03_invalid_source_receipt_goes_to_repair_branch() -> None:
    receipt = _valid_receipt()
    receipt["source_kind_ref"] = "helper_green"
    op02 = dmd.build_p7_r54_ahr_post_dmh18_dmd_op02_candidate_vs_real_operation_evidence_claim_separation(
        op18_finalizer_bodyfree_intake=_op01_ready(),
        actual_operation_evidence_receipt_bodyfree_optional=receipt,
    )
    material = dmd.build_p7_r54_ahr_post_dmh18_dmd_op03_actual_evidence_receipt_completeness_inventory(
        candidate_vs_real_operation_evidence_claim_separation=op02,
        actual_operation_evidence_receipt_bodyfree_optional=receipt,
    )

    assert material["dmd_op03_status_ref"] == dmd.P7_R54_AHR_POST_DMH18_DMD_OP03_STATUS_REPAIR_REQUIRED_REF
    assert material["actual_evidence_receipt_invalid_source_detected"] is True
    assert material["bodyfree_evidence_boundary_repair_required"] is True
    assert material["branch_candidate_ref"] == dmd.P7_R54_AHR_POST_DMH18_DMD_BRANCH_REPAIR_REQUIRED_REF
    assert material["next_required_step"] == dmd.P7_R54_AHR_POST_DMH18_DMD_NEXT_STEP_STOP_AND_REPAIR_BODYFREE_REF
    assert dmd.assert_p7_r54_ahr_post_dmh18_dmd_op03_actual_evidence_receipt_completeness_inventory_contract(material) is True
    _assert_common_bodyfree_no_touch_no_promotion(material)


def test_dmd_op03_failed_no_body_guard_goes_to_repair_branch() -> None:
    receipt = _valid_receipt()
    receipt["no_body_leak_validation_passed"] = False
    op02 = dmd.build_p7_r54_ahr_post_dmh18_dmd_op02_candidate_vs_real_operation_evidence_claim_separation(
        op18_finalizer_bodyfree_intake=_op01_ready(),
        actual_operation_evidence_receipt_bodyfree_optional=receipt,
    )
    material = dmd.build_p7_r54_ahr_post_dmh18_dmd_op03_actual_evidence_receipt_completeness_inventory(
        candidate_vs_real_operation_evidence_claim_separation=op02,
        actual_operation_evidence_receipt_bodyfree_optional=receipt,
    )

    assert material["dmd_op03_status_ref"] == dmd.P7_R54_AHR_POST_DMH18_DMD_OP03_STATUS_REPAIR_REQUIRED_REF
    assert "dmd_op03_actual_operation_evidence_receipt_bodyfree_guard_failed" in material["dmd_op03_blocker_refs"]
    assert material["bodyfree_evidence_boundary_repair_required"] is True
    assert material["next_required_step"] == dmd.P7_R54_AHR_POST_DMH18_DMD_NEXT_STEP_STOP_AND_REPAIR_BODYFREE_REF
    assert dmd.assert_p7_r54_ahr_post_dmh18_dmd_op03_actual_evidence_receipt_completeness_inventory_contract(material) is True
    _assert_common_bodyfree_no_touch_no_promotion(material)


def test_dmd_op02_forbidden_payload_receipt_goes_to_repair_without_leaking_value() -> None:
    receipt = _valid_receipt()
    receipt["raw_input"] = "body value must not leak"
    material = dmd.build_p7_r54_ahr_post_dmh18_dmd_op02_candidate_vs_real_operation_evidence_claim_separation(
        op18_finalizer_bodyfree_intake=_op01_ready(),
        actual_operation_evidence_receipt_bodyfree_optional=receipt,
    )

    assert material["dmd_op02_status_ref"] == dmd.P7_R54_AHR_POST_DMH18_DMD_OP02_STATUS_REPAIR_REQUIRED_REF
    assert material["external_actual_operation_evidence_receipt_forbidden_payload_key_paths"] == [
        "actual_operation_evidence_receipt_bodyfree_optional.raw_input"
    ]
    assert "body value must not leak" not in repr(material)
    assert material["next_required_step"] == dmd.P7_R54_AHR_POST_DMH18_DMD_NEXT_STEP_STOP_AND_REPAIR_BODYFREE_REF
    assert dmd.assert_p7_r54_ahr_post_dmh18_dmd_op02_candidate_vs_real_operation_evidence_claim_separation_contract(material) is True
    _assert_common_bodyfree_no_touch_no_promotion(material)


def test_dmd_op03_forbidden_payload_receipt_goes_to_repair_without_leaking_value() -> None:
    receipt = _valid_receipt()
    receipt["question_text"] = "question body must not leak"
    op02 = dmd.build_p7_r54_ahr_post_dmh18_dmd_op02_candidate_vs_real_operation_evidence_claim_separation(
        op18_finalizer_bodyfree_intake=_op01_ready(),
        actual_operation_evidence_receipt_bodyfree_optional=receipt,
    )
    material = dmd.build_p7_r54_ahr_post_dmh18_dmd_op03_actual_evidence_receipt_completeness_inventory(
        candidate_vs_real_operation_evidence_claim_separation=op02,
        actual_operation_evidence_receipt_bodyfree_optional=receipt,
    )

    assert material["dmd_op03_status_ref"] == dmd.P7_R54_AHR_POST_DMH18_DMD_OP03_STATUS_REPAIR_REQUIRED_REF
    assert material["actual_evidence_receipt_forbidden_payload_key_paths"] == [
        "actual_operation_evidence_receipt_bodyfree_optional.question_text"
    ]
    assert "question body must not leak" not in repr(material)
    assert material["next_required_step"] == dmd.P7_R54_AHR_POST_DMH18_DMD_NEXT_STEP_STOP_AND_REPAIR_BODYFREE_REF
    assert dmd.assert_p7_r54_ahr_post_dmh18_dmd_op03_actual_evidence_receipt_completeness_inventory_contract(material) is True
    _assert_common_bodyfree_no_touch_no_promotion(material)


def test_dmd_op03_review_session_mismatch_stays_incomplete() -> None:
    receipt = _valid_receipt()
    receipt["review_session_id"] = "different_bodyfree_session_ref"
    op02 = dmd.build_p7_r54_ahr_post_dmh18_dmd_op02_candidate_vs_real_operation_evidence_claim_separation(
        op18_finalizer_bodyfree_intake=_op01_ready(),
        actual_operation_evidence_receipt_bodyfree_optional=receipt,
    )
    material = dmd.build_p7_r54_ahr_post_dmh18_dmd_op03_actual_evidence_receipt_completeness_inventory(
        candidate_vs_real_operation_evidence_claim_separation=op02,
        actual_operation_evidence_receipt_bodyfree_optional=receipt,
    )

    assert material["dmd_op03_status_ref"] == dmd.P7_R54_AHR_POST_DMH18_DMD_OP03_STATUS_INCOMPLETE_REF
    assert material["review_session_id_consistent"] is False
    assert "dmd_op03_review_session_id_inconsistent" in material["dmd_op03_blocker_refs"]
    assert material["next_required_step"] == dmd.P7_R54_AHR_POST_DMH18_DMD_NEXT_STEP_CONTINUE_OR_RETRY_ACTUAL_REVIEW_REF
    assert dmd.assert_p7_r54_ahr_post_dmh18_dmd_op03_actual_evidence_receipt_completeness_inventory_contract(material) is True
    _assert_common_bodyfree_no_touch_no_promotion(material)


def test_dmd_op02_contract_rejects_candidate_auto_promotion_mutation() -> None:
    material = dmd.build_p7_r54_ahr_post_dmh18_dmd_op02_candidate_vs_real_operation_evidence_claim_separation(
        op18_finalizer_bodyfree_intake=_op01_ready(),
    )
    material["claimed_from_real_operation"] = True

    with pytest.raises(ValueError):
        dmd.assert_p7_r54_ahr_post_dmh18_dmd_op02_candidate_vs_real_operation_evidence_claim_separation_contract(material)


def test_dmd_op03_contract_rejects_complete_branch_downstream_manual_decision_claim_mutation() -> None:
    receipt = _valid_receipt()
    material = dmd.build_p7_r54_ahr_post_dmh18_dmd_op03_actual_evidence_receipt_completeness_inventory(
        op18_finalizer_bodyfree_intake=_op01_ready(),
        actual_operation_evidence_receipt_bodyfree_optional=receipt,
    )
    material["downstream_manual_decision_required_without_auto_execution"] = True

    with pytest.raises(ValueError):
        dmd.assert_p7_r54_ahr_post_dmh18_dmd_op03_actual_evidence_receipt_completeness_inventory_contract(material)


def test_dmd_op02_op03_alias_builders_and_contracts_match_canonical_functions() -> None:
    receipt = _valid_receipt()
    op01 = _op01_ready()
    op02 = dmd.build_p7_r54_ahr_post_dmh18_downstream_manual_decision_candidate_vs_real_operation_evidence_claim_separation(
        op18_finalizer_bodyfree_intake=op01,
        actual_operation_evidence_receipt_bodyfree_optional=receipt,
    )
    op03 = dmd.build_p7_r54_ahr_post_dmh18_downstream_manual_decision_actual_evidence_receipt_completeness_inventory(
        candidate_vs_real_operation_evidence_claim_separation=op02,
        actual_operation_evidence_receipt_bodyfree_optional=receipt,
    )

    assert op02["dmd_op02_status_ref"] == dmd.P7_R54_AHR_POST_DMH18_DMD_OP02_STATUS_REAL_OPERATION_CLAIM_SUPPORTED_REF
    assert op03["dmd_op03_status_ref"] == dmd.P7_R54_AHR_POST_DMH18_DMD_OP03_STATUS_COMPLETE_REF
    assert dmd.assert_p7_r54_ahr_post_dmh18_downstream_manual_decision_candidate_vs_real_operation_evidence_claim_separation_contract(op02) is True
    assert dmd.assert_p7_r54_ahr_post_dmh18_downstream_manual_decision_actual_evidence_receipt_completeness_inventory_contract(op03) is True
