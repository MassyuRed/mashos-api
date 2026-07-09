# -*- coding: utf-8 -*-
"""Compact body-free PNT-OP08 closure fixtures for PCM selected regression.

These fixtures keep the PCM selected-regression lane tests focused on the
explicit closed PNT-OP08 contract without re-materializing the heavy upstream
NCI/PNT chain during pytest collection.
"""

from __future__ import annotations

import emlis_ai_p7_r54_ahr_post_nci_selected_handoff_or_stop_decision_triage_20260707 as pnt


COMPACT_PNT_OP08_ALLOWED_LANE_REFS = tuple(pnt.P7_R54_AHR_POST_NCI_PNT_ALLOWED_LANE_REFS)


def build_compact_valid_closed_pnt_op08_for_pcm_regression(lane_ref: str) -> dict[str, object]:
    """Return one valid closed body-free PNT-OP08 material for PCM tests.

    The returned material intentionally satisfies the real PNT-OP08 contract and
    does not call any PNT builder, DHR-OP05 builder, downstream execution,
    actual-review, P8, API/DB/RN/runtime, or release path.
    """

    if lane_ref not in COMPACT_PNT_OP08_ALLOWED_LANE_REFS:
        raise ValueError(f"unsupported compact PNT-OP08 lane ref: {lane_ref!r}")

    status_ref = pnt.P7_R54_AHR_POST_NCI_PNT_OP08_STATUS_CLOSED_STOPPED_REF
    selected_next_ref = pnt.P7_R54_AHR_POST_NCI_PNT_LANE_TO_SELECTED_HANDOFF_OR_STOP_REF_MAP[lane_ref]
    selected_next_kind = pnt.P7_R54_AHR_POST_NCI_PNT_LANE_TO_NEXT_DESIGN_OR_STOP_KIND_REF_MAP[lane_ref]

    material: dict[str, object] = {
        "schema_version": pnt.P7_R54_AHR_POST_NCI_PNT_OP08_SCHEMA_VERSION,
        "phase": pnt.P7_R54_AHR_POST_NCI_PNT_PHASE,
        "step": pnt.P7_R54_AHR_POST_NCI_PNT_STEP,
        "scope": pnt.P7_R54_AHR_POST_NCI_PNT_SCOPE,
        "policy_kind": pnt.P7_R54_AHR_POST_NCI_PNT_POLICY_KIND,
        "policy_section": pnt.P7_R54_AHR_POST_NCI_PNT_OP08_STEP_REF,
        "operation_step_ref": pnt.P7_R54_AHR_POST_NCI_PNT_OP08_STEP_REF,
        "current_phase": pnt.P7_R54_AHR_POST_NCI_PNT_PHASE,
        "material_id": "p7_r54_ahr_post_nci_pnt_op08_compact_bodyfree_closure_for_pcm_regression_20260708",
        "review_session_id": pnt.P7_R54_AHR_POST_NCI_PNT_DEFAULT_REVIEW_SESSION_ID,
        "source_mode": pnt.P7_R54_AHR_POST_NCI_PNT_SOURCE_MODE,
        "git_connection_required": False,
        "git_checked": False,
        "op07_material_present": True,
        "op07_contract_valid": True,
        "op07_schema_version": pnt.P7_R54_AHR_POST_NCI_PNT_OP07_SCHEMA_VERSION,
        "op07_material_ref": "p7_r54_ahr_post_nci_pnt_op07_compact_bodyfree_validation_plan_for_pcm_regression",
        "op07_status_ref": pnt.P7_R54_AHR_POST_NCI_PNT_OP07_STATUS_RESULT_MEMO_DRAFT_MATERIALIZED_STOPPED_REF,
        "op07_next_required_step": pnt.P7_R54_AHR_POST_NCI_PNT_OP08_STEP_REF,
        "op07_ready_for_op08": True,
        "nci_op08_material_present": True,
        "nci_op08_contract_valid": True,
        "nci_op08_schema_version": "cocolon.emlis.p7_r54.ahr.post_rdb08.nci.op08_bodyfree_selected_candidate_intake_result_memo_closure.bodyfree.v1",
        "nci_op08_material_ref": "p7_r54_ahr_post_rdb08_nci_op08_compact_bodyfree_selected_candidate_closure_for_pcm_regression",
        "nci_op08_status_ref": "NCI_OP08_BODYFREE_SELECTED_CANDIDATE_INTAKE_RESULT_MEMO_CLOSED_STOPPED",
        "nci_op08_closed_bodyfree_stopped": True,
        "post_nci_triage_result_memo_draft_ref": "pnt_op07_compact_bodyfree_draft_for_" + selected_next_ref,
        "post_nci_triage_result_memo_draft_bodyfree": True,
        "post_nci_triage_result_memo_draft_materialized_here": True,
        "bodyfree_post_nci_triage_result_memo_closure_ref": "pnt_op08_compact_bodyfree_closure_for_" + selected_next_ref,
        "bodyfree_post_nci_triage_result_memo_closure_bodyfree": True,
        "bodyfree_post_nci_triage_result_memo_closure_materialized_here": True,
        "bodyfree_post_nci_triage_result_memo_closure_execution_allowed_here": False,
        "selected_pnt_status_ref": pnt.P7_R54_AHR_POST_NCI_PNT_LANE_TO_STATUS_REF_MAP[lane_ref],
        "selected_pnt_lane_ref": lane_ref,
        "selected_post_nci_outcome_group_ref": pnt.P7_R54_AHR_POST_NCI_PNT_LANE_TO_OUTCOME_GROUP_REF_MAP[lane_ref],
        "selected_post_nci_next_boundary_ref": selected_next_ref,
        "selected_post_nci_next_boundary_kind_ref": selected_next_kind,
        "selected_post_nci_next_boundary_not_executed": True,
        "selected_post_nci_next_boundary_execution_allowed_here": False,
        "selected_post_nci_next_boundary_materialized_here": False,
        "selected_handoff_or_stop_ref": selected_next_ref,
        "selected_handoff_or_stop_kind_ref": pnt.P7_R54_AHR_POST_NCI_PNT_LANE_TO_ENVELOPE_KIND_REF_MAP[lane_ref],
        "selected_handoff_or_stop_not_executed": True,
        "next_design_document_candidate_ref": pnt.P7_R54_AHR_POST_NCI_PNT_LANE_TO_NEXT_DESIGN_DOCUMENT_CANDIDATE_REF_MAP[lane_ref],
        "next_design_document_allowed": pnt.P7_R54_AHR_POST_NCI_PNT_LANE_TO_NEXT_DESIGN_DOCUMENT_ALLOWED_MAP[lane_ref],
        "manual_wait_required": pnt.P7_R54_AHR_POST_NCI_PNT_LANE_TO_MANUAL_WAIT_REQUIRED_MAP[lane_ref],
        "manual_stop_required": pnt.P7_R54_AHR_POST_NCI_PNT_LANE_TO_MANUAL_STOP_REQUIRED_MAP[lane_ref],
        "repair_design_candidate": pnt.P7_R54_AHR_POST_NCI_PNT_LANE_TO_REPAIR_DESIGN_CANDIDATE_MAP[lane_ref],
        "validation_plan_ref": "pnt_op07_compact_validation_plan_without_execution_for_pcm_regression",
        "validation_plan_recorded": True,
        "validation_command_summary_refs": list(pnt.P7_R54_AHR_POST_NCI_PNT_VALIDATION_COMMAND_SUMMARY_REFS),
        "validation_command_summary_ref_count": len(pnt.P7_R54_AHR_POST_NCI_PNT_VALIDATION_COMMAND_SUMMARY_REFS),
        "target_test_ref_refs": list(pnt.P7_R54_AHR_POST_NCI_PNT_TARGET_TEST_REF_REFS),
        "target_test_ref_count": len(pnt.P7_R54_AHR_POST_NCI_PNT_TARGET_TEST_REF_REFS),
        "selected_regression_test_ref_refs": list(pnt.P7_R54_AHR_POST_NCI_PNT_SELECTED_REGRESSION_TEST_REF_REFS),
        "selected_regression_test_ref_count": len(pnt.P7_R54_AHR_POST_NCI_PNT_SELECTED_REGRESSION_TEST_REF_REFS),
        "compileall_target_ref_refs": list(pnt.P7_R54_AHR_POST_NCI_PNT_COMPILEALL_TARGET_REF_REFS),
        "compileall_target_ref_count": len(pnt.P7_R54_AHR_POST_NCI_PNT_COMPILEALL_TARGET_REF_REFS),
        "target_test_result_status_ref": "pnt_op06_target_test_plan_recorded_not_executed_here",
        "selected_regression_result_status_ref": "pnt_op06_selected_regression_plan_recorded_not_executed_here",
        "compileall_result_status_ref": "pnt_op06_compileall_plan_recorded_not_executed_here",
        "full_backend_suite_green_confirmed": False,
        "rn_contract_green_confirmed": False,
        "rn_real_device_modal_verified_claimed_here": False,
        "pnt_op08_status_ref": status_ref,
        "bodyfree_post_nci_triage_result_memo_closure_status_ref": status_ref,
        "pnt_op08_allowed_status_refs": list(pnt.P7_R54_AHR_POST_NCI_PNT_OP08_ALLOWED_STATUS_REFS),
        "pnt_op08_allowed_status_ref_count": len(pnt.P7_R54_AHR_POST_NCI_PNT_OP08_ALLOWED_STATUS_REFS),
        "pnt_op08_bodyfree_post_nci_triage_closed_stopped": True,
        "pnt_op08_waiting_for_input_refs": False,
        "pnt_op08_repair_required": False,
        "pnt_op08_bodyfree_leak_promotion_or_autorun_blocked": False,
        "pnt_op08_reason_refs": [],
        "pnt_op08_reason_ref_count": 0,
        "pnt_op08_blocker_refs": [],
        "pnt_op08_blocker_ref_count": 0,
    }

    for refs_key, count_key in (
        ("op08_op07_input_forbidden_payload_key_path_refs", "op08_op07_input_forbidden_payload_key_path_count"),
        ("op08_op07_input_body_like_value_path_refs", "op08_op07_input_body_like_value_path_count"),
        ("op08_op07_input_promotion_claim_refs", "op08_op07_input_promotion_claim_ref_count"),
        ("op08_op07_input_no_touch_mutation_path_refs", "op08_op07_input_no_touch_mutation_path_count"),
        ("op08_nci_input_forbidden_payload_key_path_refs", "op08_nci_input_forbidden_payload_key_path_count"),
        ("op08_nci_input_body_like_value_path_refs", "op08_nci_input_body_like_value_path_count"),
        ("op08_nci_input_promotion_claim_refs", "op08_nci_input_promotion_claim_ref_count"),
        ("op08_nci_input_no_touch_mutation_path_refs", "op08_nci_input_no_touch_mutation_path_count"),
    ):
        material[refs_key] = []
        material[count_key] = 0

    material.update(
        {
            "selected_handoff_or_stop_execution_allowed_here": False,
            "dhr_op05_call_allowed_here": False,
            "dhr_op05_builder_call_allowed_here": False,
            "dhr_op06_call_allowed_here": False,
            "dmd_r52_execution_allowed_here": False,
            "actual_review_start_allowed_here": False,
            "raw_evidence_request_allowed_here": False,
            "repair_execution_allowed_here": False,
            "p8_question_design_allowed_here": False,
            "api_db_rn_response_key_change_allowed_here": False,
            "pnt_op08_does_not_execute_selected_handoff_or_stop": True,
            "pnt_op08_does_not_execute_selected_post_nci_next_boundary": True,
            "pnt_op08_does_not_call_dhr_op05": True,
            "pnt_op08_does_not_call_dhr_op06": True,
            "pnt_op08_does_not_execute_dmd_r52_or_release": True,
            "pnt_op08_does_not_start_actual_review": True,
            "pnt_op08_does_not_request_raw_evidence": True,
            "pnt_op08_does_not_execute_repair": True,
            "pnt_op08_does_not_start_p5_p6_p8_p7_or_release": True,
            "pnt_op08_does_not_change_api_db_rn_runtime_response_key": True,
            "pnt_op08_does_not_materialize_p8_question_spec": True,
            "dhr_op05_not_called": True,
            "dhr_op06_not_called": True,
            "dmd_r52_not_executed": True,
            "p5_p6_p8_p7_release_not_started": True,
            "p8_question_design_not_started": True,
            "p8_question_implementation_not_started": True,
            "api_db_rn_runtime_response_key_not_changed": True,
            "claim_boundary_refs": list(pnt.P7_R54_AHR_POST_NCI_PNT_CLAIM_BOUNDARY_REFS),
            "claim_boundary_ref_count": len(pnt.P7_R54_AHR_POST_NCI_PNT_CLAIM_BOUNDARY_REFS),
            "not_claimed_boundary_refs": list(pnt.P7_R54_AHR_POST_NCI_PNT_NOT_CLAIMED_BOUNDARY_REFS),
            "not_claimed_boundary_ref_count": len(pnt.P7_R54_AHR_POST_NCI_PNT_NOT_CLAIMED_BOUNDARY_REFS),
            "not_claimed_boundary": pnt._not_claimed_boundary(),
            "fixed_non_promotion_refs": list(pnt.P7_R54_AHR_POST_NCI_PNT_FIXED_NON_PROMOTION_REFS),
            "fixed_non_promotion_ref_count": len(pnt.P7_R54_AHR_POST_NCI_PNT_FIXED_NON_PROMOTION_REFS),
            "implemented_steps": list(pnt.P7_R54_AHR_POST_NCI_PNT_OP08_IMPLEMENTED_STEPS),
            "not_yet_implemented_steps": list(pnt.P7_R54_AHR_POST_NCI_PNT_OP08_NOT_YET_IMPLEMENTED_STEPS),
            "next_required_step": selected_next_ref,
            "public_contract": pnt.public_contract_flags(),
            "pnt_no_touch_contract": pnt._no_touch_contract(),
            "body_free_markers": pnt._body_free_markers(),
            **pnt._false_flags(),
            "body_free": True,
        }
    )

    assert set(material) == set(pnt.P7_R54_AHR_POST_NCI_PNT_OP08_REQUIRED_FIELD_REFS)
    assert pnt.assert_p7_r54_ahr_post_nci_pnt_op08_bodyfree_post_nci_triage_result_memo_closure_contract(material) is True
    return material


def compact_closed_pnt_op08_for_pcm_regression(index: int = 0) -> dict[str, object]:
    """Return a compact valid PNT-OP08 closure by canonical lane index."""

    return build_compact_valid_closed_pnt_op08_for_pcm_regression(COMPACT_PNT_OP08_ALLOWED_LANE_REFS[index])
