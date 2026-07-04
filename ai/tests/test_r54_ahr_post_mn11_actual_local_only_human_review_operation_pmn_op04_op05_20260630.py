# -*- coding: utf-8 -*-
"""R54-AHR Post-MN11 actual local-only human review operation PMN-OP04/OP05 tests."""

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


def test_pmn_op00_to_op03_implementation_is_present_before_op04_op05() -> None:
    op01 = _ready_op01()
    op02 = _ready_op02()
    op03 = _ready_op03()

    assert pmn.assert_p7_r54_ahr_post_mn11_pmn_op01_mn11_manual_decision_intake_basis_confirmation_contract(op01) is True
    assert pmn.assert_p7_r54_ahr_post_mn11_pmn_op02_existing_op_ex_mn_support_material_inventory_contract(op02) is True
    assert pmn.assert_p7_r54_ahr_post_mn11_pmn_op03_review_session_envelope_actual_source_guard_freeze_contract(op03) is True
    assert op03["next_required_step"] == pmn.P7_R54_AHR_POST_MN11_PMN_OP04_STEP_REF
    assert tuple(op03["implemented_steps"]) == pmn.P7_R54_AHR_POST_MN11_PMN_OP03_IMPLEMENTED_STEPS
    _assert_bodyfree_no_touch_no_promotion(op03)


def test_pmn_op04_blocks_without_ready_op03_or_explicit_allow_and_does_not_generate_packet() -> None:
    material = pmn.build_p7_r54_ahr_post_mn11_pmn_op04_local_only_preflight_explicit_allow_boundary()

    assert set(material) == set(pmn.P7_R54_AHR_POST_MN11_PMN_OP04_REQUIRED_FIELD_REFS)
    assert material["local_only_preflight_status_ref"] == pmn.P7_R54_AHR_POST_MN11_PMN_OP04_BLOCKED_STATUS_REF
    assert material["local_only_preflight_ready"] is False
    assert "pmn_op04_op03_review_session_envelope_not_ready" in material["local_only_preflight_blocker_refs"]
    assert "pmn_op04_explicit_allow_ref_missing_or_mismatched" in material["local_only_preflight_blocker_refs"]
    assert material["body_full_packet_generation_allowed_for_local_review_only"] is False
    assert material["body_full_packet_generation_allowed_by_preflight"] is False
    assert material["body_full_packet_generation_request_allowed_next"] is False
    assert material["body_full_packet_generated_here"] is False
    assert material["actual_review_evidence_complete_from_real_review"] is False
    assert tuple(material["implemented_steps"]) == pmn.P7_R54_AHR_POST_MN11_PMN_OP03_IMPLEMENTED_STEPS
    assert material["next_required_step"] == pmn.P7_R54_AHR_POST_MN11_PMN_OP04_BLOCKED_NEXT_REQUIRED_STEP_REF
    assert pmn.assert_p7_r54_ahr_post_mn11_pmn_op04_local_only_preflight_explicit_allow_boundary_contract(material) is True
    _assert_bodyfree_no_touch_no_promotion(material)


def test_pmn_op04_freezes_local_only_preflight_and_explicit_allow_boundary() -> None:
    material = _ready_op04()

    assert set(material) == set(pmn.P7_R54_AHR_POST_MN11_PMN_OP04_REQUIRED_FIELD_REFS)
    assert material["schema_version"] == pmn.P7_R54_AHR_POST_MN11_PMN_OP04_LOCAL_ONLY_PREFLIGHT_EXPLICIT_ALLOW_BOUNDARY_SCHEMA_VERSION
    assert material["operation_step_ref"] == pmn.P7_R54_AHR_POST_MN11_PMN_OP04_STEP_REF
    assert material["local_only_preflight_status_ref"] == pmn.P7_R54_AHR_POST_MN11_PMN_OP04_READY_STATUS_REF
    assert material["local_only_preflight_ready"] is True
    assert material["local_only_preflight_blocker_refs"] == []
    assert material["op03_review_session_envelope_ready"] is True
    assert material["op03_actual_source_guard_ready"] is True
    assert material["op03_review_session_state_ref"] == pmn.P7_R54_AHR_POST_MN11_REVIEW_SESSION_STATE_NOT_STARTED_REF
    assert material["local_review_root_ref_present"] is True
    assert material["local_review_root_ref_has_path_shape"] is False
    assert material["local_review_root_path_included"] is False
    assert material["explicit_allow_ref_present"] is True
    assert material["explicit_allow_body_stored_here"] is False
    assert material["retention_policy_ref_present"] is True
    assert material["disposal_policy_ref_present"] is True
    assert material["export_denylist_policy_ref_present"] is True
    assert material["export_denylist_violation_refs"] == []
    assert tuple(material["purge_required_delete_target_refs"]) == pmn.P7_R54_AHR_POST_MN11_PMN_OP04_REQUIRED_DELETE_TARGET_REFS
    assert material["local_only"] is True
    assert material["must_not_export"] is True
    assert material["body_full_packet_generation_allowed_for_local_review_only"] is True
    assert material["body_full_packet_generation_allowed_by_preflight"] is True
    assert material["body_full_packet_generation_request_allowed_next"] is False
    assert material["body_full_generation_blocked_until_manifest_refreeze"] is True
    assert material["body_full_packet_export_allowed"] is False
    assert material["body_full_packet_generated_here"] is False
    assert tuple(material["implemented_steps"]) == pmn.P7_R54_AHR_POST_MN11_PMN_OP04_IMPLEMENTED_STEPS
    assert tuple(material["not_yet_implemented_steps"]) == pmn.P7_R54_AHR_POST_MN11_PMN_OP04_NOT_YET_IMPLEMENTED_STEPS
    assert material["next_required_step"] == pmn.P7_R54_AHR_POST_MN11_PMN_OP05_STEP_REF
    assert pmn.assert_p7_r54_ahr_post_mn11_pmn_op04_local_only_preflight_explicit_allow_boundary_contract(material) is True
    _assert_bodyfree_no_touch_no_promotion(material)


@pytest.mark.parametrize(
    ("field", "bad_value"),
    (
        ("local_review_root_ref", "../not_bodyfree_path"),
        ("local_review_root_ref_has_path_shape", True),
        ("explicit_allow_ref", "missing_explicit_allow_ref"),
        ("retention_policy_ref", "wrong_retention_policy"),
        ("disposal_policy_ref", "wrong_disposal_policy"),
        ("export_denylist_policy_ref", "wrong_export_denylist_policy"),
        ("body_full_packet_generation_allowed_by_preflight", False),
        ("body_full_packet_generation_request_allowed_next", True),
        ("body_full_packet_export_allowed", True),
        ("body_full_packet_generated_here", True),
        ("p8_start_allowed", True),
    ),
)
def test_pmn_op04_contract_rejects_allow_path_export_packet_or_promotion_mutation(field: str, bad_value: object) -> None:
    material = _ready_op04()
    material[field] = bad_value
    with pytest.raises(ValueError):
        pmn.assert_p7_r54_ahr_post_mn11_pmn_op04_local_only_preflight_explicit_allow_boundary_contract(material)


def test_pmn_op05_blocks_without_ready_preflight_and_does_not_freeze_rows() -> None:
    material = pmn.build_p7_r54_ahr_post_mn11_pmn_op05_24_case_manifest_refreeze()

    assert set(material) == set(pmn.P7_R54_AHR_POST_MN11_PMN_OP05_REQUIRED_FIELD_REFS)
    assert material["manifest_status_ref"] == pmn.P7_R54_AHR_POST_MN11_PMN_OP05_BLOCKED_STATUS_REF
    assert material["manifest_ready"] is False
    assert "pmn_op05_op04_local_only_preflight_not_ready" in material["manifest_blocker_refs"]
    assert material["total_case_count"] == 0
    assert material["case_ref_id_count"] == 0
    assert material["case_manifest_rows"] == []
    assert material["controller_manifest_rows"] == []
    assert material["reviewer_facing_case_index_rows"] == []
    assert material["body_full_packet_generation_request_allowed_next"] is False
    assert material["body_full_packet_generated_here"] is False
    assert material["actual_human_review_still_not_run"] is True
    assert material["actual_review_evidence_complete_from_real_review"] is False
    assert material["next_required_step"] == pmn.P7_R54_AHR_POST_MN11_PMN_OP05_BLOCKED_NEXT_REQUIRED_STEP_REF
    assert pmn.assert_p7_r54_ahr_post_mn11_pmn_op05_24_case_manifest_refreeze_contract(material) is True
    _assert_bodyfree_no_touch_no_promotion(material)


def test_pmn_op05_refreezes_24_case_manifest_bodyfree_without_packet_generation() -> None:
    material = pmn.build_p7_r54_ahr_post_mn11_pmn_op05_24_case_manifest_refreeze(
        local_only_preflight_explicit_allow_boundary=_ready_op04()
    )

    assert set(material) == set(pmn.P7_R54_AHR_POST_MN11_PMN_OP05_REQUIRED_FIELD_REFS)
    assert material["schema_version"] == pmn.P7_R54_AHR_POST_MN11_PMN_OP05_24_CASE_MANIFEST_REFREEZE_SCHEMA_VERSION
    assert material["operation_step_ref"] == pmn.P7_R54_AHR_POST_MN11_PMN_OP05_STEP_REF
    assert material["manifest_status_ref"] == pmn.P7_R54_AHR_POST_MN11_PMN_OP05_READY_STATUS_REF
    assert material["manifest_ready"] is True
    assert material["manifest_blocker_refs"] == []
    assert material["required_case_count"] == 24
    assert material["total_case_count"] == 24
    assert material["case_ref_id_count"] == 24
    assert material["blind_case_id_count"] == 24
    assert material["packet_ref_id_count"] == 24
    assert material["selection_row_count_required"] == 24
    assert material["sanitized_review_result_row_count_required"] == 24
    assert material["rating_row_count_required"] == 24
    assert material["question_need_observation_row_count_required"] == 24
    assert material["case_distribution"] == op.P7_R54_OP05_CASE_DISTRIBUTION
    assert material["case_distribution_matches_design"] is True
    assert material["family_case_counts"] == pmn.P7_R54_AHR_POST_MN11_24_CASE_MANIFEST_DISTRIBUTION
    assert material["boundary_case_count"] == 4
    assert material["low_information_boundary_case_count"] == 2
    assert material["free_tier_boundary_case_count"] == 2
    assert material["case_ref_ids_unique"] is True
    assert material["blind_case_ids_unique"] is True
    assert material["packet_ref_ids_unique"] is True
    assert material["blind_case_id_case_ref_separated"] is True
    assert material["blind_case_id_packet_ref_separated"] is True
    assert material["case_ref_id_packet_ref_separated"] is True
    assert len(material["case_manifest_rows"]) == 24
    assert len(material["controller_manifest_rows"]) == 24
    assert len(material["reviewer_facing_case_index_rows"]) == 24
    assert material["controller_keeps_family_tier_expected_refs"] is True
    assert material["reviewer_receives_blind_case_id_only"] is True
    assert material["reviewer_facing_family_exposed"] is False
    assert material["reviewer_facing_tier_exposed"] is False
    assert material["reviewer_facing_case_ref_exposed"] is False
    assert material["reviewer_facing_packet_ref_exposed"] is False
    assert material["p4_r11_rows_confused_as_r54_review_rows"] is False
    assert material["p4_r11_rows_mixed_in"] is False
    assert material["body_full_packet_generation_request_allowed_next"] is True
    assert material["body_full_packet_generated_here"] is False
    assert material["body_full_packet_materialized_here"] is False
    assert material["actual_human_review_still_not_run"] is True
    assert material["actual_review_evidence_complete_from_real_review"] is False
    assert tuple(material["implemented_steps"]) == pmn.P7_R54_AHR_POST_MN11_PMN_OP05_IMPLEMENTED_STEPS
    assert tuple(material["not_yet_implemented_steps"]) == pmn.P7_R54_AHR_POST_MN11_PMN_OP05_NOT_YET_IMPLEMENTED_STEPS
    assert material["next_required_step"] == pmn.P7_R54_AHR_POST_MN11_PMN_OP06_STEP_REF
    assert pmn.assert_p7_r54_ahr_post_mn11_pmn_op05_24_case_manifest_refreeze_contract(material) is True
    _assert_bodyfree_no_touch_no_promotion(material)


@pytest.mark.parametrize(
    ("field", "bad_value"),
    (
        ("total_case_count", 23),
        ("case_ref_id_count", 23),
        ("case_distribution", {"history_line_eligible_input": 24}),
        ("case_distribution_matches_design", False),
        ("p4_r11_rows_confused_as_r54_review_rows", True),
        ("p4_r11_rows_mixed_in", True),
        ("body_full_packet_generation_request_allowed_next", False),
        ("body_full_packet_generated_here", True),
        ("actual_review_evidence_complete_from_real_review", True),
        ("p8_start_allowed", True),
    ),
)
def test_pmn_op05_contract_rejects_manifest_packet_evidence_or_promotion_mutation(field: str, bad_value: object) -> None:
    material = pmn.build_p7_r54_ahr_post_mn11_pmn_op05_24_case_manifest_refreeze(
        local_only_preflight_explicit_allow_boundary=_ready_op04()
    )
    material[field] = bad_value
    with pytest.raises(ValueError):
        pmn.assert_p7_r54_ahr_post_mn11_pmn_op05_24_case_manifest_refreeze_contract(material)


def test_pmn_op05_contract_rejects_reviewer_facing_hidden_metadata_exposure() -> None:
    material = pmn.build_p7_r54_ahr_post_mn11_pmn_op05_24_case_manifest_refreeze(
        local_only_preflight_explicit_allow_boundary=_ready_op04()
    )
    mutated = deepcopy(material)
    mutated["reviewer_facing_case_index_rows"][0]["family_exposed"] = True
    with pytest.raises(ValueError):
        pmn.assert_p7_r54_ahr_post_mn11_pmn_op05_24_case_manifest_refreeze_contract(mutated)


def test_pmn_op05_contract_rejects_case_row_bodyfull_materialization() -> None:
    material = pmn.build_p7_r54_ahr_post_mn11_pmn_op05_24_case_manifest_refreeze(
        local_only_preflight_explicit_allow_boundary=_ready_op04()
    )
    mutated = deepcopy(material)
    mutated["case_manifest_rows"][0]["body_full_packet_materialized_here"] = True
    with pytest.raises(ValueError):
        pmn.assert_p7_r54_ahr_post_mn11_pmn_op05_24_case_manifest_refreeze_contract(mutated)


def test_pmn_op04_op05_aliases_match_primary_builders_and_contracts() -> None:
    op03 = _ready_op03()
    primary_op04 = pmn.build_p7_r54_ahr_post_mn11_pmn_op04_local_only_preflight_explicit_allow_boundary(
        review_session_envelope_actual_source_guard_freeze=op03,
        local_review_root_ref=pmn.P7_R54_AHR_POST_MN11_PMN_OP04_LOCAL_REVIEW_ROOT_REF,
        explicit_allow_ref=pmn.P7_R54_AHR_POST_MN11_PMN_OP04_EXPLICIT_ALLOW_REF,
        retention_policy_ref=pmn.P7_R54_AHR_POST_MN11_PMN_OP04_RETENTION_POLICY_REF,
        disposal_policy_ref=pmn.P7_R54_AHR_POST_MN11_PMN_OP04_DISPOSAL_POLICY_REF,
        export_denylist_policy_ref=pmn.P7_R54_AHR_POST_MN11_PMN_OP04_EXPORT_DENYLIST_POLICY_REF,
    )
    alias_op04 = pmn.build_p7_r54_ahr_post_mn11_actual_operation_local_only_preflight_explicit_allow_boundary_bodyfree(
        review_session_envelope_actual_source_guard_freeze=op03,
        local_review_root_ref=pmn.P7_R54_AHR_POST_MN11_PMN_OP04_LOCAL_REVIEW_ROOT_REF,
        explicit_allow_ref=pmn.P7_R54_AHR_POST_MN11_PMN_OP04_EXPLICIT_ALLOW_REF,
        retention_policy_ref=pmn.P7_R54_AHR_POST_MN11_PMN_OP04_RETENTION_POLICY_REF,
        disposal_policy_ref=pmn.P7_R54_AHR_POST_MN11_PMN_OP04_DISPOSAL_POLICY_REF,
        export_denylist_policy_ref=pmn.P7_R54_AHR_POST_MN11_PMN_OP04_EXPORT_DENYLIST_POLICY_REF,
    )
    assert alias_op04 == primary_op04
    assert pmn.assert_p7_r54_ahr_post_mn11_actual_operation_local_only_preflight_explicit_allow_boundary_bodyfree_contract(alias_op04) is True

    primary_op05 = pmn.build_p7_r54_ahr_post_mn11_pmn_op05_24_case_manifest_refreeze(
        local_only_preflight_explicit_allow_boundary=primary_op04
    )
    alias_op05 = pmn.build_p7_r54_ahr_post_mn11_actual_operation_24_case_manifest_refreeze_bodyfree(
        local_only_preflight_explicit_allow_boundary=primary_op04
    )
    assert alias_op05 == primary_op05
    assert pmn.assert_p7_r54_ahr_post_mn11_actual_operation_24_case_manifest_refreeze_bodyfree_contract(alias_op05) is True
