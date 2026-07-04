# -*- coding: utf-8 -*-
"""R54-AHR Post-DMH18 downstream manual decision triage DMD-OP06/OP07 tests."""

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
        "operation_receipt_ref": "dmd_op06_op07_actual_operation_receipt_bodyfree_fixture_001",
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


def _op02_missing() -> dict[str, object]:
    material = dmd.build_p7_r54_ahr_post_dmh18_dmd_op02_candidate_vs_real_operation_evidence_claim_separation(
        op18_finalizer_bodyfree_intake=_op01_ready(),
    )
    assert dmd.assert_p7_r54_ahr_post_dmh18_dmd_op02_candidate_vs_real_operation_evidence_claim_separation_contract(material) is True
    return material


def _op03_missing() -> dict[str, object]:
    material = dmd.build_p7_r54_ahr_post_dmh18_dmd_op03_actual_evidence_receipt_completeness_inventory(
        candidate_vs_real_operation_evidence_claim_separation=_op02_missing(),
    )
    assert dmd.assert_p7_r54_ahr_post_dmh18_dmd_op03_actual_evidence_receipt_completeness_inventory_contract(material) is True
    return material


def _complete_chain() -> tuple[dict[str, object], dict[str, object], dict[str, object], dict[str, object]]:
    receipt = _valid_receipt()
    op02 = dmd.build_p7_r54_ahr_post_dmh18_dmd_op02_candidate_vs_real_operation_evidence_claim_separation(
        op18_finalizer_bodyfree_intake=_op01_ready(),
        actual_operation_evidence_receipt_bodyfree_optional=receipt,
    )
    assert dmd.assert_p7_r54_ahr_post_dmh18_dmd_op02_candidate_vs_real_operation_evidence_claim_separation_contract(op02) is True
    op03 = dmd.build_p7_r54_ahr_post_dmh18_dmd_op03_actual_evidence_receipt_completeness_inventory(
        candidate_vs_real_operation_evidence_claim_separation=op02,
        actual_operation_evidence_receipt_bodyfree_optional=receipt,
    )
    assert dmd.assert_p7_r54_ahr_post_dmh18_dmd_op03_actual_evidence_receipt_completeness_inventory_contract(op03) is True
    op04 = dmd.build_p7_r54_ahr_post_dmh18_dmd_op04_bodyfree_leak_invalid_source_scan(
        actual_evidence_receipt_completeness_inventory=op03,
        actual_operation_evidence_receipt_bodyfree_optional=receipt,
    )
    assert dmd.assert_p7_r54_ahr_post_dmh18_dmd_op04_bodyfree_leak_invalid_source_scan_contract(op04) is True
    op05 = dmd.build_p7_r54_ahr_post_dmh18_dmd_op05_downstream_promotion_claim_scan(
        bodyfree_leak_invalid_source_scan=op04,
    )
    assert dmd.assert_p7_r54_ahr_post_dmh18_dmd_op05_downstream_promotion_claim_scan_contract(op05) is True
    return op02, op03, op04, op05


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


def test_dmd_op06_current_missing_receipt_resolves_branch_a_continue_or_retry() -> None:
    op02 = _op02_missing()
    op03 = _op03_missing()
    op04 = dmd.build_p7_r54_ahr_post_dmh18_dmd_op04_bodyfree_leak_invalid_source_scan(
        actual_evidence_receipt_completeness_inventory=op03,
    )
    op05 = dmd.build_p7_r54_ahr_post_dmh18_dmd_op05_downstream_promotion_claim_scan(
        bodyfree_leak_invalid_source_scan=op04,
    )
    material = dmd.build_p7_r54_ahr_post_dmh18_dmd_op06_deterministic_branch_resolver(
        downstream_promotion_claim_scan=op05,
        actual_evidence_receipt_completeness_inventory=op03,
        candidate_vs_real_operation_evidence_claim_separation=op02,
    )

    assert set(material) == set(dmd.P7_R54_AHR_POST_DMH18_DMD_OP06_REQUIRED_FIELD_REFS)
    assert material["schema_version"] == dmd.P7_R54_AHR_POST_DMH18_DMD_OP06_SCHEMA_VERSION
    assert material["dmd_op06_status_ref"] == dmd.P7_R54_AHR_POST_DMH18_DMD_OP06_STATUS_EVIDENCE_INCOMPLETE_REF
    assert material["branch_ref"] == dmd.P7_R54_AHR_POST_DMH18_DMD_BRANCH_EVIDENCE_INCOMPLETE_REF
    assert material["candidate_supported"] is True
    assert material["claimed_from_real_operation"] is False
    assert material["evidence_incomplete_continue_or_retry_required"] is True
    assert material["bodyfree_evidence_boundary_repair_required"] is False
    assert material["downstream_manual_decision_required_without_auto_execution"] is False
    assert material["next_required_step"] == dmd.P7_R54_AHR_POST_DMH18_DMD_NEXT_STEP_CONTINUE_OR_RETRY_ACTUAL_REVIEW_REF
    assert "dmd_op06_real_operation_evidence_claim_not_present" in material["branch_blocker_refs"]
    assert tuple(material["implemented_steps"]) == dmd.P7_R54_AHR_POST_DMH18_DMD_OP06_IMPLEMENTED_STEPS
    assert dmd.assert_p7_r54_ahr_post_dmh18_dmd_op06_deterministic_branch_resolver_contract(material) is True
    _assert_common_bodyfree_no_touch_no_promotion(material)


def test_dmd_op07_current_missing_receipt_materializes_branch_a_without_downstream_execution() -> None:
    op06 = dmd.build_p7_r54_ahr_post_dmh18_dmd_op06_deterministic_branch_resolver(
        actual_evidence_receipt_completeness_inventory=_op03_missing(),
        candidate_vs_real_operation_evidence_claim_separation=_op02_missing(),
    )
    material = dmd.build_p7_r54_ahr_post_dmh18_dmd_op07_manual_decision_materialization(
        deterministic_branch_resolver=op06,
    )

    assert set(material) == set(dmd.P7_R54_AHR_POST_DMH18_DMD_OP07_REQUIRED_FIELD_REFS)
    assert material["schema_version"] == dmd.P7_R54_AHR_POST_DMH18_DMD_OP07_SCHEMA_VERSION
    assert material["dmd_op07_status_ref"] == dmd.P7_R54_AHR_POST_DMH18_DMD_OP07_STATUS_EVIDENCE_INCOMPLETE_REF
    assert material["manual_decision_materialized"] is True
    assert material["branch_ref"] == dmd.P7_R54_AHR_POST_DMH18_DMD_BRANCH_EVIDENCE_INCOMPLETE_REF
    assert material["candidate_supported"] is True
    assert material["claimed_from_real_operation"] is False
    assert material["next_required_step"] == dmd.P7_R54_AHR_POST_DMH18_DMD_NEXT_STEP_CONTINUE_OR_RETRY_ACTUAL_REVIEW_REF
    assert material["downstream_manual_decision_required_without_auto_execution"] is False
    assert tuple(material["implemented_steps"]) == dmd.P7_R54_AHR_POST_DMH18_DMD_OP07_IMPLEMENTED_STEPS
    assert dmd.assert_p7_r54_ahr_post_dmh18_dmd_op07_manual_decision_materialization_contract(material) is True
    _assert_common_bodyfree_no_touch_no_promotion(material)


def test_dmd_op06_complete_receipt_resolves_branch_c_no_auto_execution() -> None:
    op02, op03, _op04, op05 = _complete_chain()
    material = dmd.build_p7_r54_ahr_post_dmh18_dmd_op06_deterministic_branch_resolver(
        downstream_promotion_claim_scan=op05,
        actual_evidence_receipt_completeness_inventory=op03,
        candidate_vs_real_operation_evidence_claim_separation=op02,
    )

    assert material["dmd_op06_status_ref"] == dmd.P7_R54_AHR_POST_DMH18_DMD_OP06_STATUS_EVIDENCE_COMPLETE_REF
    assert material["branch_ref"] == dmd.P7_R54_AHR_POST_DMH18_DMD_BRANCH_EVIDENCE_COMPLETE_MANUAL_DECISION_NO_AUTO_EXEC_REF
    assert material["candidate_supported"] is True
    assert material["claimed_from_real_operation"] is True
    assert material["complete_branch_selected_after_no_repair_no_incomplete"] is True
    assert material["branch_blocker_refs"] == []
    assert material["downstream_manual_decision_required_without_auto_execution"] is True
    assert material["next_required_step"] == dmd.P7_R54_AHR_POST_DMH18_DMD_NEXT_STEP_DOWNSTREAM_MANUAL_DECISION_NO_AUTO_EXEC_REF
    assert material["postcr22_ex07_ex18_reentry_executed_here"] is False
    assert material["r52_actual_execution_started_here"] is False
    assert material["p5_final_allowed"] is False
    assert material["p6_start_allowed"] is False
    assert material["p8_start_allowed"] is False
    assert material["p7_complete"] is False
    assert material["release_allowed"] is False
    assert dmd.assert_p7_r54_ahr_post_dmh18_dmd_op06_deterministic_branch_resolver_contract(material) is True
    _assert_common_bodyfree_no_touch_no_promotion(material)


def test_dmd_op07_complete_receipt_materializes_branch_c_but_still_no_promotion() -> None:
    op02, op03, _op04, op05 = _complete_chain()
    op06 = dmd.build_p7_r54_ahr_post_dmh18_dmd_op06_deterministic_branch_resolver(
        downstream_promotion_claim_scan=op05,
        actual_evidence_receipt_completeness_inventory=op03,
        candidate_vs_real_operation_evidence_claim_separation=op02,
    )
    material = dmd.build_p7_r54_ahr_post_dmh18_dmd_op07_manual_decision_materialization(
        deterministic_branch_resolver=op06,
    )

    assert material["dmd_op07_status_ref"] == dmd.P7_R54_AHR_POST_DMH18_DMD_OP07_STATUS_EVIDENCE_COMPLETE_REF
    assert material["branch_ref"] == dmd.P7_R54_AHR_POST_DMH18_DMD_BRANCH_EVIDENCE_COMPLETE_MANUAL_DECISION_NO_AUTO_EXEC_REF
    assert material["candidate_supported"] is True
    assert material["claimed_from_real_operation"] is True
    assert material["downstream_manual_decision_required_without_auto_execution"] is True
    assert material["postcr22_ex07_ex18_reentry_ready_candidate_carried_without_execution"] is True
    assert material["r52_handoff_candidate_carried_without_execution"] is True
    assert material["postcr22_ex07_ex18_reentry_executed_here"] is False
    assert material["r52_actual_execution_started_here"] is False
    assert material["r52_actual_execution_confirmed"] is False
    assert material["p5_final_allowed"] is False
    assert material["p6_start_allowed"] is False
    assert material["p8_start_allowed"] is False
    assert material["p8_question_design_started"] is False
    assert material["p8_question_implementation_started"] is False
    assert material["p7_complete"] is False
    assert material["release_allowed"] is False
    assert dmd.assert_p7_r54_ahr_post_dmh18_dmd_op07_manual_decision_materialization_contract(material) is True
    _assert_common_bodyfree_no_touch_no_promotion(material)


def test_dmd_op06_repair_precedence_over_complete_candidate_when_promotion_claim_detected() -> None:
    op02, op03, op04, _op05 = _complete_chain()
    promoted_optional = {"p8_start_allowed": True}
    op05 = dmd.build_p7_r54_ahr_post_dmh18_dmd_op05_downstream_promotion_claim_scan(
        bodyfree_leak_invalid_source_scan=op04,
        downstream_manual_decision_material_optional=promoted_optional,
    )
    assert op05["dmd_op05_status_ref"] == dmd.P7_R54_AHR_POST_DMH18_DMD_OP05_STATUS_REPAIR_REQUIRED_REF
    material = dmd.build_p7_r54_ahr_post_dmh18_dmd_op06_deterministic_branch_resolver(
        downstream_promotion_claim_scan=op05,
        actual_evidence_receipt_completeness_inventory=op03,
        candidate_vs_real_operation_evidence_claim_separation=op02,
    )

    assert material["dmd_op06_status_ref"] == dmd.P7_R54_AHR_POST_DMH18_DMD_OP06_STATUS_REPAIR_REQUIRED_REF
    assert material["branch_ref"] == dmd.P7_R54_AHR_POST_DMH18_DMD_BRANCH_REPAIR_REQUIRED_REF
    assert material["repair_precedence_applied"] is True
    assert material["complete_branch_selected_after_no_repair_no_incomplete"] is False
    assert material["bodyfree_evidence_boundary_repair_required"] is True
    assert material["next_required_step"] == dmd.P7_R54_AHR_POST_DMH18_DMD_NEXT_STEP_STOP_AND_REPAIR_BODYFREE_REF
    assert "dmd_op05_downstream_promotion_claim_detected" in material["branch_blocker_refs"]
    assert dmd.assert_p7_r54_ahr_post_dmh18_dmd_op06_deterministic_branch_resolver_contract(material) is True
    _assert_common_bodyfree_no_touch_no_promotion(material)


def test_dmd_op07_repair_branch_materializes_stop_and_repair_only() -> None:
    op02, op03, op04, _op05 = _complete_chain()
    op05 = dmd.build_p7_r54_ahr_post_dmh18_dmd_op05_downstream_promotion_claim_scan(
        bodyfree_leak_invalid_source_scan=op04,
        downstream_manual_decision_material_optional={"r52_actual_execution_confirmed": True},
    )
    op06 = dmd.build_p7_r54_ahr_post_dmh18_dmd_op06_deterministic_branch_resolver(
        downstream_promotion_claim_scan=op05,
        actual_evidence_receipt_completeness_inventory=op03,
        candidate_vs_real_operation_evidence_claim_separation=op02,
    )
    material = dmd.build_p7_r54_ahr_post_dmh18_dmd_op07_manual_decision_materialization(
        deterministic_branch_resolver=op06,
    )

    assert material["dmd_op07_status_ref"] == dmd.P7_R54_AHR_POST_DMH18_DMD_OP07_STATUS_REPAIR_REQUIRED_REF
    assert material["branch_ref"] == dmd.P7_R54_AHR_POST_DMH18_DMD_BRANCH_REPAIR_REQUIRED_REF
    assert material["bodyfree_evidence_boundary_repair_required"] is True
    assert material["evidence_incomplete_continue_or_retry_required"] is False
    assert material["downstream_manual_decision_required_without_auto_execution"] is False
    assert material["next_required_step"] == dmd.P7_R54_AHR_POST_DMH18_DMD_NEXT_STEP_STOP_AND_REPAIR_BODYFREE_REF
    assert material["p8_start_allowed"] is False
    assert material["r52_actual_execution_confirmed"] is False
    assert material["release_allowed"] is False
    assert dmd.assert_p7_r54_ahr_post_dmh18_dmd_op07_manual_decision_materialization_contract(material) is True
    _assert_common_bodyfree_no_touch_no_promotion(material)


def test_dmd_op06_rejects_resolver_priority_tampering() -> None:
    material = dmd.build_p7_r54_ahr_post_dmh18_dmd_op06_deterministic_branch_resolver(
        actual_evidence_receipt_completeness_inventory=_op03_missing(),
        candidate_vs_real_operation_evidence_claim_separation=_op02_missing(),
    )
    material["resolver_priority_refs"] = list(reversed(material["resolver_priority_refs"]))

    with pytest.raises(ValueError):
        dmd.assert_p7_r54_ahr_post_dmh18_dmd_op06_deterministic_branch_resolver_contract(material)


def test_dmd_op07_rejects_auto_execution_and_fixed_non_promotion_tampering() -> None:
    op06 = dmd.build_p7_r54_ahr_post_dmh18_dmd_op06_deterministic_branch_resolver(
        actual_evidence_receipt_completeness_inventory=_op03_missing(),
        candidate_vs_real_operation_evidence_claim_separation=_op02_missing(),
    )
    material = dmd.build_p7_r54_ahr_post_dmh18_dmd_op07_manual_decision_materialization(
        deterministic_branch_resolver=op06,
    )
    promoted = deepcopy(material)
    promoted["manual_decision_auto_executes_downstream"] = True
    with pytest.raises(ValueError):
        dmd.assert_p7_r54_ahr_post_dmh18_dmd_op07_manual_decision_materialization_contract(promoted)

    tampered = deepcopy(material)
    tampered["fixed_non_promotion_refs"] = list(tampered["fixed_non_promotion_refs"][:-1])
    tampered["fixed_non_promotion_ref_count"] = len(tampered["fixed_non_promotion_refs"])
    with pytest.raises(ValueError):
        dmd.assert_p7_r54_ahr_post_dmh18_dmd_op07_manual_decision_materialization_contract(tampered)
