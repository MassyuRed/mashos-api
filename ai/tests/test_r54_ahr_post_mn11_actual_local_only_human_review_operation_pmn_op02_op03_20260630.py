# -*- coding: utf-8 -*-
"""R54-AHR Post-MN11 actual local-only human review operation PMN-OP02/OP03 tests."""

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


def test_pmn_op00_op01_implementation_is_present_before_op02_op03() -> None:
    op00 = pmn.build_p7_r54_ahr_post_mn11_pmn_op00_scope_no_touch_no_promotion_boundary_freeze()
    op01 = _ready_op01()

    assert pmn.assert_p7_r54_ahr_post_mn11_pmn_op00_scope_no_touch_no_promotion_boundary_freeze_contract(op00) is True
    assert pmn.assert_p7_r54_ahr_post_mn11_pmn_op01_mn11_manual_decision_intake_basis_confirmation_contract(op01) is True
    assert tuple(op01["implemented_steps"]) == pmn.P7_R54_AHR_POST_MN11_PMN_OP01_IMPLEMENTED_STEPS
    assert op01["next_required_step"] == pmn.P7_R54_AHR_POST_MN11_PMN_OP02_STEP_REF
    assert op01["mn11_actual_review_basis_ref"] == "current_received_snapshot_264_85_258_171"
    _assert_bodyfree_no_touch_no_promotion(op01)


def test_pmn_op02_blocks_without_ready_op01_and_does_not_claim_inventory_ready() -> None:
    material = pmn.build_p7_r54_ahr_post_mn11_pmn_op02_existing_op_ex_mn_support_material_inventory()

    assert set(material) == set(pmn.P7_R54_AHR_POST_MN11_PMN_OP02_REQUIRED_FIELD_REFS)
    assert material["support_inventory_status_ref"] == pmn.P7_R54_AHR_POST_MN11_PMN_OP02_BLOCKED_STATUS_REF
    assert material["support_inventory_ready"] is False
    assert "pmn_op02_op01_mn11_intake_not_ready" in material["support_inventory_blocker_refs"]
    assert material["existing_op_line_reuse_candidate"] is False
    assert material["existing_ex_line_reentry_candidate"] is False
    assert material["existing_mn_line_manual_decision_intake_candidate"] is False
    assert material["minimal_bridge_allowed_if_needed"] is False
    assert material["new_giant_wrapper_required"] is False
    assert material["next_required_step"] == pmn.P7_R54_AHR_POST_MN11_PMN_OP02_BLOCKED_NEXT_REQUIRED_STEP_REF
    assert pmn.assert_p7_r54_ahr_post_mn11_pmn_op02_existing_op_ex_mn_support_material_inventory_contract(material) is True
    _assert_bodyfree_no_touch_no_promotion(material)


def test_pmn_op02_inventories_existing_op_ex_mn_material_as_minimal_bridge_candidates() -> None:
    material = _ready_op02()

    assert set(material) == set(pmn.P7_R54_AHR_POST_MN11_PMN_OP02_REQUIRED_FIELD_REFS)
    assert material["schema_version"] == pmn.P7_R54_AHR_POST_MN11_PMN_OP02_EXISTING_OP_EX_MN_SUPPORT_MATERIAL_INVENTORY_SCHEMA_VERSION
    assert material["operation_step_ref"] == pmn.P7_R54_AHR_POST_MN11_PMN_OP02_STEP_REF
    assert material["support_inventory_status_ref"] == pmn.P7_R54_AHR_POST_MN11_PMN_OP02_READY_STATUS_REF
    assert material["support_inventory_ready"] is True
    assert material["support_inventory_blocker_refs"] == []
    assert material["op01_ready"] is True
    assert material["op01_next_required_step"] == pmn.P7_R54_AHR_POST_MN11_PMN_OP02_STEP_REF
    assert material["existing_op_line_step_refs"][0] == op.P7_R54_OP00_STEP_REF
    assert material["existing_op_line_step_refs"][-1] == op.P7_R54_OP24_STEP_REF
    assert material["existing_op_line_step_ref_count"] == 25
    assert material["existing_op_line_reuse_candidate"] is True
    assert material["existing_ex_line_reentry_step_refs"][0] == ex.P7_R54_AHR_POST_CR22_EX07_STEP_REF
    assert material["existing_ex_line_reentry_step_refs"][-1] == ex.P7_R54_AHR_POST_CR22_EX18_STEP_REF
    assert material["existing_ex_line_reentry_step_ref_count"] == 12
    assert material["existing_ex_line_reentry_candidate"] is True
    assert material["existing_mn_line_step_refs"][0] == mn.P7_R54_AHR_POST_EX18_MN00_STEP_REF
    assert material["existing_mn_line_step_refs"][-1] == mn.P7_R54_AHR_POST_EX18_MN11_STEP_REF
    assert material["existing_mn_line_step_ref_count"] == 12
    assert material["existing_mn_line_manual_decision_intake_candidate"] is True
    assert material["new_giant_wrapper_required"] is False
    assert material["minimal_bridge_allowed_if_needed"] is True
    assert tuple(material["implemented_steps"]) == pmn.P7_R54_AHR_POST_MN11_PMN_OP02_IMPLEMENTED_STEPS
    assert tuple(material["not_yet_implemented_steps"]) == pmn.P7_R54_AHR_POST_MN11_PMN_OP02_NOT_YET_IMPLEMENTED_STEPS
    assert material["next_required_step"] == pmn.P7_R54_AHR_POST_MN11_PMN_OP03_STEP_REF
    assert pmn.assert_p7_r54_ahr_post_mn11_pmn_op02_existing_op_ex_mn_support_material_inventory_contract(material) is True
    _assert_bodyfree_no_touch_no_promotion(material)


@pytest.mark.parametrize(
    ("field", "bad_value"),
    (
        ("new_giant_wrapper_required", True),
        ("existing_op_line_reuse_candidate", False),
        ("existing_ex_line_reentry_candidate", False),
        ("existing_mn_line_manual_decision_intake_candidate", False),
        ("actual_review_basis_ref", "latest_zip_label_not_actual_basis"),
        ("p8_start_allowed", True),
    ),
)
def test_pmn_op02_contract_rejects_giant_wrapper_promotion_or_basis_mutation(field: str, bad_value: object) -> None:
    material = _ready_op02()
    material[field] = bad_value
    with pytest.raises(ValueError):
        pmn.assert_p7_r54_ahr_post_mn11_pmn_op02_existing_op_ex_mn_support_material_inventory_contract(material)


def test_pmn_op02_contract_rejects_support_line_range_mutation() -> None:
    material = _ready_op02()
    material["existing_ex_line_reentry_step_refs"] = list(material["existing_ex_line_reentry_step_refs"][:-1])
    material["existing_ex_line_reentry_step_ref_count"] = len(material["existing_ex_line_reentry_step_refs"])
    with pytest.raises(ValueError):
        pmn.assert_p7_r54_ahr_post_mn11_pmn_op02_existing_op_ex_mn_support_material_inventory_contract(material)


def test_pmn_op03_blocks_without_ready_support_inventory_and_does_not_start_session() -> None:
    material = pmn.build_p7_r54_ahr_post_mn11_pmn_op03_review_session_envelope_actual_source_guard_freeze()

    assert set(material) == set(pmn.P7_R54_AHR_POST_MN11_PMN_OP03_REQUIRED_FIELD_REFS)
    assert material["review_session_envelope_status_ref"] == pmn.P7_R54_AHR_POST_MN11_PMN_OP03_BLOCKED_STATUS_REF
    assert material["actual_source_guard_status_ref"] == pmn.P7_R54_AHR_POST_MN11_PMN_OP03_BLOCKED_STATUS_REF
    assert material["review_session_envelope_ready"] is False
    assert material["actual_source_guard_ready"] is False
    assert "pmn_op03_support_inventory_not_ready" in material["actual_source_guard_step_blocker_refs"]
    assert material["review_session_state_ref"] == pmn.P7_R54_AHR_POST_MN11_REVIEW_SESSION_STATE_NOT_STARTED_REF
    assert material["actual_rows_source_guard_passed"] is False
    assert material["actual_rows_intaked_here"] is False
    assert material["next_required_step"] == pmn.P7_R54_AHR_POST_MN11_PMN_OP03_BLOCKED_NEXT_REQUIRED_STEP_REF
    assert pmn.assert_p7_r54_ahr_post_mn11_pmn_op03_review_session_envelope_actual_source_guard_freeze_contract(material) is True
    _assert_bodyfree_no_touch_no_promotion(material)


def test_pmn_op03_freezes_review_session_envelope_and_actual_source_guard() -> None:
    material = pmn.build_p7_r54_ahr_post_mn11_pmn_op03_review_session_envelope_actual_source_guard_freeze(
        existing_op_ex_mn_support_material_inventory=_ready_op02()
    )

    assert set(material) == set(pmn.P7_R54_AHR_POST_MN11_PMN_OP03_REQUIRED_FIELD_REFS)
    assert material["schema_version"] == pmn.P7_R54_AHR_POST_MN11_PMN_OP03_REVIEW_SESSION_ENVELOPE_ACTUAL_SOURCE_GUARD_FREEZE_SCHEMA_VERSION
    assert material["operation_step_ref"] == pmn.P7_R54_AHR_POST_MN11_PMN_OP03_STEP_REF
    assert material["review_session_envelope_status_ref"] == pmn.P7_R54_AHR_POST_MN11_PMN_OP03_READY_STATUS_REF
    assert material["actual_source_guard_status_ref"] == pmn.P7_R54_AHR_POST_MN11_PMN_OP03_READY_STATUS_REF
    assert material["review_session_envelope_ready"] is True
    assert material["actual_source_guard_ready"] is True
    assert material["review_session_envelope_blocker_refs"] == []
    assert material["actual_source_guard_step_blocker_refs"] == []
    assert material["review_session_id"] == pmn.P7_R54_AHR_POST_MN11_DEFAULT_REVIEW_SESSION_ID
    assert material["review_session_id_bodyfree_identifier"] is True
    assert material["review_session_id_has_local_path_shape"] is False
    assert material["review_session_id_has_question_or_body_text_shape"] is False
    assert tuple(material["allowed_actual_source_refs"]) == pmn.P7_R54_AHR_POST_MN11_ALLOWED_ACTUAL_SOURCE_REFS
    assert tuple(material["forbidden_actual_source_refs"]) == pmn.P7_R54_AHR_POST_MN11_FORBIDDEN_ACTUAL_SOURCE_REFS
    assert not set(material["allowed_actual_source_refs"]).intersection(material["forbidden_actual_source_refs"])
    assert material["actual_source_guard_blocks_helper_default_rows"] is True
    assert material["actual_source_guard_blocks_unit_test_rows"] is True
    assert material["actual_source_guard_blocks_synthetic_rows"] is True
    assert material["actual_source_guard_blocks_historical_rows"] is True
    assert material["actual_source_guard_requires_person_read_receipt_later"] is True
    for key in pmn.P7_R54_AHR_POST_MN11_SOURCE_GUARD_REQUIRED_FALSE_FIELD_REFS:
        assert material[key] is False, key
    assert material["actual_rows_source_guard_passed"] is False
    assert material["actual_rows_intaked_here"] is False
    assert tuple(material["implemented_steps"]) == pmn.P7_R54_AHR_POST_MN11_PMN_OP03_IMPLEMENTED_STEPS
    assert tuple(material["not_yet_implemented_steps"]) == pmn.P7_R54_AHR_POST_MN11_PMN_OP03_NOT_YET_IMPLEMENTED_STEPS
    assert material["next_required_step"] == pmn.P7_R54_AHR_POST_MN11_PMN_OP04_STEP_REF
    assert pmn.assert_p7_r54_ahr_post_mn11_pmn_op03_review_session_envelope_actual_source_guard_freeze_contract(material) is True
    _assert_bodyfree_no_touch_no_promotion(material)


@pytest.mark.parametrize(
    ("field", "bad_value"),
    (
        ("helper_default_rows_allowed_as_actual", True),
        ("unit_test_rows_allowed_as_actual", True),
        ("synthetic_contract_fixture_rows_allowed_as_actual", True),
        ("historical_rows_allowed_as_actual", True),
        ("actual_source_guard_materializes_actual_rows_here", True),
        ("actual_source_guard_runs_actual_human_review_here", True),
        ("actual_rows_source_guard_passed", True),
        ("actual_rows_intaked_here", True),
        ("p8_start_allowed", True),
    ),
)
def test_pmn_op03_contract_rejects_actual_source_guard_promotion_or_rows(field: str, bad_value: object) -> None:
    material = pmn.build_p7_r54_ahr_post_mn11_pmn_op03_review_session_envelope_actual_source_guard_freeze(
        existing_op_ex_mn_support_material_inventory=_ready_op02()
    )
    material[field] = bad_value
    with pytest.raises(ValueError):
        pmn.assert_p7_r54_ahr_post_mn11_pmn_op03_review_session_envelope_actual_source_guard_freeze_contract(material)


def test_pmn_op03_contract_rejects_allowed_forbidden_source_ref_mutation() -> None:
    material = pmn.build_p7_r54_ahr_post_mn11_pmn_op03_review_session_envelope_actual_source_guard_freeze(
        existing_op_ex_mn_support_material_inventory=_ready_op02()
    )
    material["allowed_actual_source_refs"] = list(material["forbidden_actual_source_refs"])
    material["allowed_actual_source_ref_count"] = len(material["allowed_actual_source_refs"])
    with pytest.raises(ValueError):
        pmn.assert_p7_r54_ahr_post_mn11_pmn_op03_review_session_envelope_actual_source_guard_freeze_contract(material)


def test_pmn_op03_contract_rejects_review_session_shape_or_state_mutation() -> None:
    material = pmn.build_p7_r54_ahr_post_mn11_pmn_op03_review_session_envelope_actual_source_guard_freeze(
        existing_op_ex_mn_support_material_inventory=_ready_op02()
    )

    mutated = deepcopy(material)
    mutated["review_session_id_has_local_path_shape"] = True
    with pytest.raises(ValueError):
        pmn.assert_p7_r54_ahr_post_mn11_pmn_op03_review_session_envelope_actual_source_guard_freeze_contract(mutated)

    mutated = deepcopy(material)
    mutated["review_session_state_ref"] = "REVIEW_IN_PROGRESS_LOCAL_ONLY"
    with pytest.raises(ValueError):
        pmn.assert_p7_r54_ahr_post_mn11_pmn_op03_review_session_envelope_actual_source_guard_freeze_contract(mutated)


def test_pmn_op02_op03_aliases_match_primary_builders_and_contracts() -> None:
    op01 = _ready_op01()
    primary_op02 = pmn.build_p7_r54_ahr_post_mn11_pmn_op02_existing_op_ex_mn_support_material_inventory(
        mn11_manual_decision_intake_basis_confirmation=op01
    )
    alias_op02 = pmn.build_p7_r54_ahr_post_mn11_actual_operation_existing_op_ex_mn_support_material_inventory_bodyfree(
        mn11_manual_decision_intake_basis_confirmation=op01
    )
    assert alias_op02 == primary_op02
    assert pmn.assert_p7_r54_ahr_post_mn11_actual_operation_existing_op_ex_mn_support_material_inventory_bodyfree_contract(alias_op02) is True

    primary_op03 = pmn.build_p7_r54_ahr_post_mn11_pmn_op03_review_session_envelope_actual_source_guard_freeze(
        existing_op_ex_mn_support_material_inventory=primary_op02
    )
    alias_op03 = pmn.build_p7_r54_ahr_post_mn11_actual_operation_review_session_envelope_actual_source_guard_freeze_bodyfree(
        existing_op_ex_mn_support_material_inventory=primary_op02
    )
    assert alias_op03 == primary_op03
    assert pmn.assert_p7_r54_ahr_post_mn11_actual_operation_review_session_envelope_actual_source_guard_freeze_bodyfree_contract(alias_op03) is True
