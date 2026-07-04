# -*- coding: utf-8 -*-
"""R54-AHR Post-MN11 actual local-only human review operation PMN-OP06/OP07 tests."""

from __future__ import annotations

from copy import deepcopy

import pytest

import emlis_ai_p7_r54_actual_local_review_operation_reentry_20260625 as op
import emlis_ai_p7_r54_ahr_post_cr22_actual_local_review_execution_evidence_completion_20260629 as ex
import emlis_ai_p7_r54_ahr_post_ex18_manual_next_decision_return_to_actual_review_operation_20260630 as mn
import emlis_ai_p7_r54_ahr_post_mn11_actual_local_only_human_review_operation_20260630 as pmn


def _assert_bodyfree_no_touch_no_promotion(material: dict[str, object]) -> None:
    assert material["body_free"] is True
    for key in pmn.P7_R54_AHR_POST_MN11_REQUIRED_FALSE_FLAG_REFS:
        assert material[key] is False, key
    for marker_map_key in ("public_contract", "post_mn11_no_touch_contract", "body_free_markers"):
        assert material[marker_map_key]
        assert all(value is False for value in material[marker_map_key].values()), marker_map_key
    for forbidden_key in pmn.P7_R54_AHR_POST_MN11_FORBIDDEN_PAYLOAD_KEY_REFS:
        assert forbidden_key not in material, forbidden_key
    if "not_claimed_boundary" in material:
        assert all(value is False for value in material["not_claimed_boundary"].values())


def _valid_ex18_bodyfree_envelope() -> dict[str, object]:
    return {
        "schema_version": ex.P7_R54_AHR_POST_CR22_EX18_VALIDATION_COMMAND_MATRIX_RESULT_MEMO_NEXT_DECISION_HOLD_SCHEMA_VERSION,
        "operation_step_ref": ex.P7_R54_AHR_POST_CR22_EX18_STEP_REF,
        "body_free": True,
        "next_required_step": ex.P7_R54_AHR_POST_CR22_EX18_NEXT_DECISION_HOLD_REF,
        "next_decision_hold_required": True,
        "next_decision_auto_execution_allowed": False,
        "result_memo_ready": True,
        "validation_command_matrix_ready": True,
        "actual_review_evidence_complete": True,
        "actual_human_review_run_here": False,
        "actual_human_review_operation_run": False,
        "actual_human_review_newly_run_here": False,
        "actual_human_review_complete": False,
        "actual_selection_rows_created_here": False,
        "actual_rating_rows_materialized_here": True,
        "actual_question_need_observation_rows_materialized_here": True,
        "actual_disposal_receipt_materialized_here": True,
        "disposal_verified": True,
        "row_counts": {
            "reviewed_case_count": 24,
            "sanitized_review_result_row_count": 24,
            "rating_row_count": 24,
            "question_need_observation_row_count": 24,
        },
        "candidate_only_decisions": [
            "P5_CONFIRMED_CANDIDATE_BODYFREE_ONLY",
            "P6_LIMITED_HUMAN_READFEEL_CANDIDATE_ONLY",
            "P8_QUESTION_NEED_OBSERVATION_MATERIAL_CANDIDATE_ONLY",
            "R52_REINTAKE_HANDOFF_CANDIDATE_ONLY",
        ],
        "not_claimed_boundary": {key: False for key in mn.P7_R54_AHR_POST_EX18_NOT_CLAIMED_BOUNDARY_REFS},
    }


def _valid_mn01() -> dict[str, object]:
    mn00 = mn.build_p7_r54_ahr_post_ex18_mn00_scope_no_touch_no_promotion_boundary_freeze()
    return mn.build_p7_r54_ahr_post_ex18_mn01_ex18_result_memo_bodyfree_envelope_intake(
        scope_no_touch_no_promotion_boundary_freeze=mn00,
        ex18_result_memo_bodyfree_envelope=_valid_ex18_bodyfree_envelope(),
    )


def _ready_mn03() -> dict[str, object]:
    mn02 = mn.build_p7_r54_ahr_post_ex18_mn02_actual_review_evidence_state_normalization(
        ex18_result_memo_bodyfree_envelope_intake=_valid_mn01()
    )
    return mn.build_p7_r54_ahr_post_ex18_mn03_manual_decision_classifier(
        actual_review_evidence_state_normalization=mn02
    )


def _ready_mn04() -> dict[str, object]:
    return mn.build_p7_r54_ahr_post_ex18_mn04_return_to_actual_review_operation_plan(
        manual_decision_classifier=_ready_mn03()
    )


def _ready_mn05() -> dict[str, object]:
    return mn.build_p7_r54_ahr_post_ex18_mn05_expected_bodyfree_evidence_intake_bundle_boundary(
        return_to_actual_review_operation_plan=_ready_mn04()
    )


def _ready_mn06() -> dict[str, object]:
    return mn.build_p7_r54_ahr_post_ex18_mn06_no_body_no_question_no_path_no_hash_scan(
        expected_bodyfree_evidence_intake_bundle_boundary=_ready_mn05(),
        manual_decision_material=_ready_mn03(),
        return_to_actual_review_operation_plan=_ready_mn04(),
    )


def _ready_mn07() -> dict[str, object]:
    return mn.build_p7_r54_ahr_post_ex18_mn07_downstream_no_promotion_boundary_materialization(
        no_body_no_question_no_path_no_hash_scan=_ready_mn06()
    )


def _ready_mn08() -> dict[str, object]:
    return mn.build_p7_r54_ahr_post_ex18_mn08_reentry_mapping_to_existing_postcr22_ex07_ex18(
        downstream_no_promotion_boundary_materialization=_ready_mn07()
    )


def _ready_mn09() -> dict[str, object]:
    return mn.build_p7_r54_ahr_post_ex18_mn09_validation_command_matrix_result_memo_envelope(
        reentry_mapping_to_existing_postcr22_ex07_ex18=_ready_mn08()
    )


def _ready_mn10() -> dict[str, object]:
    return mn.build_p7_r54_ahr_post_ex18_mn10_alias_contract_function_boundary(
        validation_command_matrix_result_memo_envelope=_ready_mn09()
    )


def _ready_mn11() -> dict[str, object]:
    return mn.build_p7_r54_ahr_post_ex18_mn11_acceptance_fail_closed_finalizer(
        alias_contract_function_boundary=_ready_mn10()
    )


def _ready_op01() -> dict[str, object]:
    return pmn.build_p7_r54_ahr_post_mn11_pmn_op01_mn11_manual_decision_intake_basis_confirmation(
        mn11_manual_decision_material=_ready_mn11()
    )


def _ready_op02() -> dict[str, object]:
    return pmn.build_p7_r54_ahr_post_mn11_pmn_op02_existing_op_ex_mn_support_material_inventory(
        mn11_manual_decision_intake_basis_confirmation=_ready_op01()
    )


def _ready_op03() -> dict[str, object]:
    return pmn.build_p7_r54_ahr_post_mn11_pmn_op03_review_session_envelope_actual_source_guard_freeze(
        existing_op_ex_mn_support_material_inventory=_ready_op02()
    )


def _ready_op04() -> dict[str, object]:
    return pmn.build_p7_r54_ahr_post_mn11_pmn_op04_local_only_preflight_explicit_allow_boundary(
        review_session_envelope_actual_source_guard_freeze=_ready_op03(),
        local_review_root_ref=pmn.P7_R54_AHR_POST_MN11_PMN_OP04_LOCAL_REVIEW_ROOT_REF,
        explicit_allow_ref=pmn.P7_R54_AHR_POST_MN11_PMN_OP04_EXPLICIT_ALLOW_REF,
        retention_policy_ref=pmn.P7_R54_AHR_POST_MN11_PMN_OP04_RETENTION_POLICY_REF,
        disposal_policy_ref=pmn.P7_R54_AHR_POST_MN11_PMN_OP04_DISPOSAL_POLICY_REF,
        export_denylist_policy_ref=pmn.P7_R54_AHR_POST_MN11_PMN_OP04_EXPORT_DENYLIST_POLICY_REF,
    )




def _ready_op05() -> dict[str, object]:
    return pmn.build_p7_r54_ahr_post_mn11_pmn_op05_24_case_manifest_refreeze(
        local_only_preflight_explicit_allow_boundary=_ready_op04()
    )


def _ready_op06() -> dict[str, object]:
    return pmn.build_p7_r54_ahr_post_mn11_pmn_op06_body_full_packet_generation_request_bodyfree_builder(
        case_manifest_refreeze=_ready_op05()
    )


def _ready_op07() -> dict[str, object]:
    return pmn.build_p7_r54_ahr_post_mn11_pmn_op07_packet_generation_local_operation_receipt_boundary(
        packet_generation_request_bodyfree_builder=_ready_op06()
    )


def test_pmn_op00_to_op05_implementation_is_present_before_op06_op07() -> None:
    op01 = _ready_op01()
    op02 = _ready_op02()
    op03 = _ready_op03()
    op04 = _ready_op04()
    op05 = _ready_op05()

    assert pmn.assert_p7_r54_ahr_post_mn11_pmn_op01_mn11_manual_decision_intake_basis_confirmation_contract(op01) is True
    assert pmn.assert_p7_r54_ahr_post_mn11_pmn_op02_existing_op_ex_mn_support_material_inventory_contract(op02) is True
    assert pmn.assert_p7_r54_ahr_post_mn11_pmn_op03_review_session_envelope_actual_source_guard_freeze_contract(op03) is True
    assert pmn.assert_p7_r54_ahr_post_mn11_pmn_op04_local_only_preflight_explicit_allow_boundary_contract(op04) is True
    assert pmn.assert_p7_r54_ahr_post_mn11_pmn_op05_24_case_manifest_refreeze_contract(op05) is True
    assert op05["next_required_step"] == pmn.P7_R54_AHR_POST_MN11_PMN_OP06_STEP_REF
    assert tuple(op05["implemented_steps"]) == pmn.P7_R54_AHR_POST_MN11_PMN_OP05_IMPLEMENTED_STEPS
    assert op05["actual_human_review_still_not_run"] is True
    assert op05["actual_review_evidence_complete_from_real_review"] is False
    _assert_bodyfree_no_touch_no_promotion(op05)


def test_pmn_op06_blocks_without_ready_manifest_and_does_not_generate_packet() -> None:
    material = pmn.build_p7_r54_ahr_post_mn11_pmn_op06_body_full_packet_generation_request_bodyfree_builder()

    assert set(material) == set(pmn.P7_R54_AHR_POST_MN11_PMN_OP06_REQUIRED_FIELD_REFS)
    assert material["packet_generation_request_status_ref"] == pmn.P7_R54_AHR_POST_MN11_PMN_OP06_BLOCKED_STATUS_REF
    assert material["packet_generation_request_ready"] is False
    assert "pmn_op06_op05_manifest_not_ready" in material["packet_generation_request_blocker_refs"]
    assert material["packet_generation_request_ref"] == ""
    assert material["packet_generation_request_bodyfree_payload"] == {}
    assert material["packet_generation_request_bodyfree_payload_field_count"] == 0
    assert material["case_manifest_ready"] is False
    assert material["case_manifest_row_count"] == 0
    assert material["case_ref_id_count"] == 0
    assert material["blind_case_id_count"] == 0
    assert material["packet_ref_id_count"] == 0
    assert material["local_only_required"] is False
    assert material["must_not_export"] is False
    assert material["packet_completeness_scan_required"] is False
    assert material["export_denylist_scan_required"] is False
    assert material["purge_required"] is False
    assert material["body_full_packet_generation_request_built_here"] is False
    assert material["packet_generation_local_operation_receipt_required_next"] is False
    assert material["body_full_packet_generation_executed_here"] is False
    assert material["body_full_packet_generated_here"] is False
    assert material["body_full_packet_materialized_here"] is False
    assert tuple(material["implemented_steps"]) == pmn.P7_R54_AHR_POST_MN11_PMN_OP05_IMPLEMENTED_STEPS
    assert material["next_required_step"] == pmn.P7_R54_AHR_POST_MN11_PMN_OP06_BLOCKED_NEXT_REQUIRED_STEP_REF
    assert pmn.assert_p7_r54_ahr_post_mn11_pmn_op06_body_full_packet_generation_request_bodyfree_builder_contract(material) is True
    _assert_bodyfree_no_touch_no_promotion(material)


def test_pmn_op06_builds_bodyfree_packet_generation_request_without_packet_content() -> None:
    material = _ready_op06()

    assert set(material) == set(pmn.P7_R54_AHR_POST_MN11_PMN_OP06_REQUIRED_FIELD_REFS)
    assert material["schema_version"] == pmn.P7_R54_AHR_POST_MN11_PMN_OP06_BODY_FULL_PACKET_GENERATION_REQUEST_BODYFREE_BUILDER_SCHEMA_VERSION
    assert material["operation_step_ref"] == pmn.P7_R54_AHR_POST_MN11_PMN_OP06_STEP_REF
    assert material["packet_generation_request_status_ref"] == pmn.P7_R54_AHR_POST_MN11_PMN_OP06_READY_STATUS_REF
    assert material["packet_generation_request_ready"] is True
    assert material["packet_generation_request_blocker_refs"] == []
    assert material["packet_generation_request_ref"] == pmn.P7_R54_AHR_POST_MN11_PMN_OP06_PACKET_GENERATION_REQUEST_REF
    assert tuple(material["packet_generation_request_reason_refs"]) == pmn.P7_R54_AHR_POST_MN11_PMN_OP06_READY_REASON_REFS
    assert material["case_manifest_ready"] is True
    assert material["case_manifest_row_count"] == 24
    assert material["case_ref_id_count"] == 24
    assert material["blind_case_id_count"] == 24
    assert material["packet_ref_id_count"] == 24
    assert material["explicit_allow_ref"] == pmn.P7_R54_AHR_POST_MN11_PMN_OP04_EXPLICIT_ALLOW_REF
    assert material["explicit_allow_ref_matches_op04"] is True
    assert material["local_only_required"] is True
    assert material["must_not_export"] is True
    assert material["packet_completeness_scan_required"] is True
    assert material["export_denylist_scan_required"] is True
    assert material["purge_required"] is True
    assert material["body_full_packet_generation_allowed_for_local_review_only"] is True
    assert material["body_full_packet_generation_request_built_here"] is True
    assert material["body_full_packet_generation_request_bodyfree_only"] is True
    assert material["body_full_packet_generation_request_allowed_next"] is False
    assert material["packet_generation_local_operation_receipt_required_next"] is True
    assert material["body_full_packet_generation_executed_here"] is False
    assert material["body_full_packet_generated_here"] is False
    assert material["body_full_packet_materialized_here"] is False
    assert material["body_full_packet_export_allowed"] is False
    assert material["body_full_packet_exported_to_artifact"] is False
    assert material["local_absolute_path_included"] is False
    assert material["body_hash_stored"] is False
    assert material["terminal_output_body_included"] is False
    assert material["actual_human_review_still_not_run"] is True
    assert material["actual_review_evidence_complete_from_real_review"] is False
    assert material["actual_review_evidence_complete_from_real_review_still_false"] is True
    assert tuple(material["implemented_steps"]) == pmn.P7_R54_AHR_POST_MN11_PMN_OP06_IMPLEMENTED_STEPS
    assert tuple(material["not_yet_implemented_steps"]) == pmn.P7_R54_AHR_POST_MN11_PMN_OP06_NOT_YET_IMPLEMENTED_STEPS
    assert material["next_required_step"] == pmn.P7_R54_AHR_POST_MN11_PMN_OP07_STEP_REF

    payload = material["packet_generation_request_bodyfree_payload"]
    assert payload == {
        "packet_generation_request_ref": pmn.P7_R54_AHR_POST_MN11_PMN_OP06_PACKET_GENERATION_REQUEST_REF,
        "review_session_id": material["review_session_id"],
        "actual_review_basis_ref": pmn.P7_R54_AHR_POST_MN11_ACTUAL_REVIEW_BASIS_REF,
        "required_case_count": 24,
        "case_manifest_ref": pmn.P7_R54_AHR_POST_MN11_PMN_OP06_CASE_MANIFEST_REF,
        "explicit_allow_ref": pmn.P7_R54_AHR_POST_MN11_PMN_OP04_EXPLICIT_ALLOW_REF,
        "local_only_required": True,
        "must_not_export": True,
        "packet_completeness_scan_required": True,
        "export_denylist_scan_required": True,
        "purge_required": True,
        "body_free": True,
    }
    assert material["packet_generation_request_contains_forbidden_payload_key"] is False
    assert material["packet_generation_request_forbidden_payload_key_paths"] == []
    assert pmn.assert_p7_r54_ahr_post_mn11_pmn_op06_body_full_packet_generation_request_bodyfree_builder_contract(material) is True
    _assert_bodyfree_no_touch_no_promotion(material)


@pytest.mark.parametrize(
    ("field", "bad_value"),
    [
        ("case_manifest_row_count", 23),
        ("body_full_packet_generation_request_bodyfree_only", False),
        ("packet_generation_request_contains_forbidden_payload_key", True),
        ("body_full_packet_generation_request_allowed_next", True),
        ("body_full_packet_generation_executed_here", True),
        ("body_full_packet_generated_here", True),
        ("body_full_packet_materialized_here", True),
        ("body_full_packet_export_allowed", True),
        ("body_full_packet_exported_to_artifact", True),
        ("local_absolute_path_included", True),
        ("body_hash_stored", True),
        ("terminal_output_body_included", True),
        ("actual_review_evidence_complete_from_real_review", True),
        ("p8_start_allowed", True),
    ],
)
def test_pmn_op06_contract_rejects_request_packet_or_promotion_mutation(field: str, bad_value: object) -> None:
    material = _ready_op06()
    mutated = deepcopy(material)
    mutated[field] = bad_value

    with pytest.raises(ValueError):
        pmn.assert_p7_r54_ahr_post_mn11_pmn_op06_body_full_packet_generation_request_bodyfree_builder_contract(mutated)


def test_pmn_op06_contract_rejects_payload_key_or_count_mutation() -> None:
    material = _ready_op06()
    mutated = deepcopy(material)
    mutated["packet_generation_request_bodyfree_payload"]["local_absolute_path"] = "forbidden"
    mutated["packet_generation_request_forbidden_payload_key_paths"] = ["payload.local_absolute_path"]
    mutated["packet_generation_request_forbidden_payload_key_path_count"] = 1
    mutated["packet_generation_request_contains_forbidden_payload_key"] = True

    with pytest.raises(ValueError):
        pmn.assert_p7_r54_ahr_post_mn11_pmn_op06_body_full_packet_generation_request_bodyfree_builder_contract(mutated)


def test_pmn_op07_blocks_without_ready_op06_and_does_not_accept_receipt() -> None:
    material = pmn.build_p7_r54_ahr_post_mn11_pmn_op07_packet_generation_local_operation_receipt_boundary()

    assert set(material) == set(pmn.P7_R54_AHR_POST_MN11_PMN_OP07_REQUIRED_FIELD_REFS)
    assert material["packet_generation_receipt_boundary_status_ref"] == pmn.P7_R54_AHR_POST_MN11_PMN_OP07_BLOCKED_STATUS_REF
    assert material["packet_generation_receipt_boundary_ready"] is False
    assert "pmn_op07_op06_packet_generation_request_not_ready" in material["packet_generation_receipt_boundary_blocker_refs"]
    assert material["packet_generation_receipt_boundary_ref"] == ""
    assert material["expected_packet_generation_receipt_ref"] == ""
    assert material["packet_generation_receipt_required_after_external_local_generation"] is False
    assert material["packet_generation_receipt_received_here"] is False
    assert material["packet_generation_receipt_intaked_here"] is False
    assert material["packet_generation_local_operation_receipt_boundary_defined_here"] is False
    assert material["packet_completeness_scan_required_next"] is False
    assert material["export_denylist_scan_required_next"] is False
    assert material["packet_count"] == 0
    assert material["packet_ref_id_count"] == 0
    assert material["packet_materialized_local_only"] is False
    assert material["body_full_packet_generation_executed_here"] is False
    assert material["body_full_packet_generated_here"] is False
    assert material["body_full_packet_materialized_here"] is False
    assert tuple(material["implemented_steps"]) == pmn.P7_R54_AHR_POST_MN11_PMN_OP06_IMPLEMENTED_STEPS
    assert material["next_required_step"] == pmn.P7_R54_AHR_POST_MN11_PMN_OP07_BLOCKED_NEXT_REQUIRED_STEP_REF
    assert pmn.assert_p7_r54_ahr_post_mn11_pmn_op07_packet_generation_local_operation_receipt_boundary_contract(material) is True
    _assert_bodyfree_no_touch_no_promotion(material)


def test_pmn_op07_freezes_local_operation_receipt_boundary_without_materializing_receipt_or_packet() -> None:
    material = _ready_op07()

    assert set(material) == set(pmn.P7_R54_AHR_POST_MN11_PMN_OP07_REQUIRED_FIELD_REFS)
    assert material["schema_version"] == pmn.P7_R54_AHR_POST_MN11_PMN_OP07_PACKET_GENERATION_LOCAL_OPERATION_RECEIPT_BOUNDARY_SCHEMA_VERSION
    assert material["operation_step_ref"] == pmn.P7_R54_AHR_POST_MN11_PMN_OP07_STEP_REF
    assert material["packet_generation_receipt_boundary_status_ref"] == pmn.P7_R54_AHR_POST_MN11_PMN_OP07_READY_STATUS_REF
    assert material["packet_generation_receipt_boundary_ready"] is True
    assert material["packet_generation_receipt_boundary_blocker_refs"] == []
    assert tuple(material["packet_generation_receipt_boundary_reason_refs"]) == pmn.P7_R54_AHR_POST_MN11_PMN_OP07_READY_REASON_REFS
    assert material["op06_packet_generation_request_ready"] is True
    assert material["op06_next_required_step"] == pmn.P7_R54_AHR_POST_MN11_PMN_OP07_STEP_REF
    assert material["op06_packet_generation_request_ref"] == pmn.P7_R54_AHR_POST_MN11_PMN_OP06_PACKET_GENERATION_REQUEST_REF
    assert material["packet_generation_receipt_boundary_ref"] == pmn.P7_R54_AHR_POST_MN11_PMN_OP07_PACKET_GENERATION_RECEIPT_BOUNDARY_REF
    assert material["expected_packet_generation_receipt_ref"] == pmn.P7_R54_AHR_POST_MN11_PMN_OP07_EXPECTED_PACKET_GENERATION_RECEIPT_REF
    assert material["packet_generation_receipt_required_after_external_local_generation"] is True
    assert material["packet_generation_receipt_received_here"] is False
    assert material["packet_generation_receipt_intaked_here"] is False
    assert material["packet_generation_receipt_actual_source_ref_required"] is True
    assert material["packet_generation_receipt_expected_actual_source_ref"] == pmn.P7_R54_AHR_POST_MN11_PMN_OP07_ACTUAL_SOURCE_REF
    assert material["packet_generation_local_operation_receipt_boundary_defined_here"] is True
    assert material["packet_generation_local_operation_receipt_bodyfree_only"] is True
    assert material["expected_packet_count"] == 24
    assert material["packet_count"] == 0
    assert material["packet_ref_id_count"] == 0
    assert material["packet_materialized_local_only"] is False
    assert material["packet_materialized_local_only_claimed_here"] is False
    assert material["packet_completeness_scan_required_next"] is True
    assert material["export_denylist_scan_required_next"] is True
    assert material["body_full_packet_generation_executed_here"] is False
    assert material["body_full_packet_generated_here"] is False
    assert material["body_full_packet_materialized_here"] is False
    assert material["body_full_packet_exported_to_artifact"] is False
    assert material["body_full_packet_export_allowed"] is False
    assert material["local_absolute_path_included"] is False
    assert material["body_hash_stored"] is False
    assert material["terminal_output_body_included"] is False
    assert material["packet_content_included"] is False
    assert material["actual_human_review_still_not_run"] is True
    assert material["actual_review_evidence_complete_from_real_review"] is False
    assert tuple(material["implemented_steps"]) == pmn.P7_R54_AHR_POST_MN11_PMN_OP07_IMPLEMENTED_STEPS
    assert tuple(material["not_yet_implemented_steps"]) == pmn.P7_R54_AHR_POST_MN11_PMN_OP07_NOT_YET_IMPLEMENTED_STEPS
    assert material["next_required_step"] == pmn.P7_R54_AHR_POST_MN11_PMN_OP08_STEP_REF
    assert pmn.assert_p7_r54_ahr_post_mn11_pmn_op07_packet_generation_local_operation_receipt_boundary_contract(material) is True
    _assert_bodyfree_no_touch_no_promotion(material)


@pytest.mark.parametrize(
    ("field", "bad_value"),
    [
        ("packet_generation_local_operation_receipt_bodyfree_only", False),
        ("packet_generation_receipt_received_here", True),
        ("packet_generation_receipt_intaked_here", True),
        ("packet_materialized_local_only", True),
        ("packet_materialized_local_only_claimed_here", True),
        ("body_full_packet_generation_executed_here", True),
        ("body_full_packet_generated_here", True),
        ("body_full_packet_materialized_here", True),
        ("body_full_packet_exported_to_artifact", True),
        ("body_full_packet_export_allowed", True),
        ("local_absolute_path_included", True),
        ("body_hash_stored", True),
        ("terminal_output_body_included", True),
        ("packet_content_included", True),
        ("actual_review_evidence_complete_from_real_review", True),
        ("p8_start_allowed", True),
    ],
)
def test_pmn_op07_contract_rejects_receipt_packet_or_promotion_mutation(field: str, bad_value: object) -> None:
    material = _ready_op07()
    mutated = deepcopy(material)
    mutated[field] = bad_value

    with pytest.raises(ValueError):
        pmn.assert_p7_r54_ahr_post_mn11_pmn_op07_packet_generation_local_operation_receipt_boundary_contract(mutated)


def test_pmn_op07_contract_rejects_packet_count_claim_before_actual_generation() -> None:
    material = _ready_op07()
    mutated = deepcopy(material)
    mutated["packet_count"] = 24
    mutated["packet_ref_id_count"] = 24

    with pytest.raises(ValueError):
        pmn.assert_p7_r54_ahr_post_mn11_pmn_op07_packet_generation_local_operation_receipt_boundary_contract(mutated)


def test_pmn_op06_op07_aliases_match_primary_builders_and_contracts() -> None:
    op05 = _ready_op05()
    primary_op06 = pmn.build_p7_r54_ahr_post_mn11_pmn_op06_body_full_packet_generation_request_bodyfree_builder(
        case_manifest_refreeze=op05
    )
    alias_op06 = pmn.build_p7_r54_ahr_post_mn11_actual_operation_body_full_packet_generation_request_bodyfree_builder(
        case_manifest_refreeze=op05
    )
    assert alias_op06 == primary_op06
    assert pmn.assert_p7_r54_ahr_post_mn11_actual_operation_body_full_packet_generation_request_bodyfree_builder_contract(alias_op06) is True

    primary_op07 = pmn.build_p7_r54_ahr_post_mn11_pmn_op07_packet_generation_local_operation_receipt_boundary(
        packet_generation_request_bodyfree_builder=primary_op06
    )
    alias_op07 = pmn.build_p7_r54_ahr_post_mn11_actual_operation_packet_generation_local_operation_receipt_boundary_bodyfree(
        packet_generation_request_bodyfree_builder=primary_op06
    )
    assert alias_op07 == primary_op07
    assert pmn.assert_p7_r54_ahr_post_mn11_actual_operation_packet_generation_local_operation_receipt_boundary_bodyfree_contract(alias_op07) is True
