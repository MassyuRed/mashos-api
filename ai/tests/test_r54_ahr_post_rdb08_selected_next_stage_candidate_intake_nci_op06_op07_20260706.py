# -*- coding: utf-8 -*-
"""R54-AHR Post-RDB08 selected next-stage candidate intake NCI-OP06/OP07 tests."""

from __future__ import annotations

from copy import deepcopy
from pathlib import Path
import sys

import pytest

TEST_DIR = Path(__file__).resolve().parent
if str(TEST_DIR) not in sys.path:
    sys.path.insert(0, str(TEST_DIR))

import emlis_ai_p7_r54_ahr_post_rdb08_selected_next_stage_candidate_intake_20260706 as nci
import emlis_ai_p7_r54_ahr_post_mrb08_dhr_op04_result_manual_decision_20260705 as rdb
from test_r54_ahr_post_dri_dhr_op04_manual_reintake_mrb_op06_op07_20260705 import (
    _op05_confirmed,
    _op05_invalid_result,
    _op05_not_confirmed,
    _op05_waiting_result,
)
from test_r54_ahr_post_mrb08_dhr_op04_result_manual_decision_rdb_op08_result_20260705 import (
    _op08_from_op05,
)

LANE_FLAG_KEYS = (
    "dhr_op05_design_target_candidate_present",
    "retry_or_start_route_candidate_present",
    "external_claim_wait_candidate_present",
    "repair_route_candidate_present",
    "unresolved_manual_hold_candidate_present",
    "blocked_candidate_present",
)

FORBIDDEN_EXECUTION_KEYS = (
    "dhr_op05_call_allowed_here",
    "dhr_op05_builder_called_here",
    "dhr_op06_builder_called_here",
    "dmd_builder_called_here",
    "r52_actual_execution_called_here",
    "actual_local_human_review_operation_started_here",
    "raw_evidence_request_created_here",
    "repair_executed_here",
    "p8_question_design_started_here",
    "p8_question_implementation_started_here",
    "question_text_materialized",
    "p8_question_substitution_allowed",
)

TRUE_BOUNDARY_KEYS_OP06 = (
    "nci_op06_does_not_execute_selected_next_stage_candidate",
    "nci_op06_does_not_call_dhr_op05",
    "nci_op06_does_not_call_dhr_op06",
    "nci_op06_does_not_execute_dmd_r52_or_release",
    "nci_op06_does_not_start_actual_review",
    "nci_op06_does_not_start_p8_question_design",
    "nci_op06_does_not_change_api_db_rn_runtime_response_key",
    "op06_does_not_execute_validation_commands",
)

TRUE_BOUNDARY_KEYS_OP07 = (
    "nci_op07_does_not_execute_handoff_or_stop_envelope",
    "nci_op07_does_not_execute_selected_next_stage_candidate",
    "nci_op07_does_not_call_dhr_op05",
    "nci_op07_does_not_start_actual_review",
    "nci_op07_does_not_request_raw_evidence",
    "nci_op07_does_not_execute_repair",
    "nci_op07_does_not_start_p8_question_design",
    "nci_op07_does_not_change_api_db_rn_runtime_response_key",
)


def _assert_common_bodyfree_no_touch_no_promotion(material: dict[str, object]) -> None:
    assert material["source_mode"] == nci.P7_R54_AHR_POST_RDB08_NCI_SOURCE_MODE
    assert material["git_connection_required"] is False
    assert material["git_checked"] is False
    assert material["body_free"] is True
    assert material["public_contract"] == nci.public_contract_flags()
    assert all(value is False for value in material["nci_no_touch_contract"].values())
    assert all(value is False for value in material["body_free_markers"].values())
    assert all(value is False for value in material["not_claimed_boundary"].values())
    for key in nci.P7_R54_AHR_POST_RDB08_NCI_REQUIRED_FALSE_FLAG_REFS:
        assert material[key] is False, key


def _assert_no_downstream_execution(material: dict[str, object]) -> None:
    for key in FORBIDDEN_EXECUTION_KEYS:
        assert material[key] is False, key
    assert material["p5_final_allowed"] is False
    assert material["p6_start_allowed"] is False
    assert material["p8_start_allowed"] is False
    assert material["release_allowed"] is False
    assert material["full_backend_suite_green_confirmed"] is False
    assert material["rn_contract_green_confirmed"] is False
    assert material["rn_real_device_modal_verified_claimed_here"] is False


def _op01_from_op05(op05: dict[str, object]) -> dict[str, object]:
    return nci.build_p7_r54_ahr_post_rdb08_nci_op01_rdb_op08_bodyfree_result_memo_closure_intake(
        rdb_op08_bodyfree_result_memo_closure=_op08_from_op05(op05),
    )


def _op01_with_selected_candidate_shape(
    *,
    rdb_status_ref: str,
    candidate_ref: str,
    candidate_kind_ref: str,
    decision_lane_ref: str,
) -> dict[str, object]:
    op01 = deepcopy(_op01_from_op05(_op05_confirmed()))
    op01.update(
        {
            "rdb_selected_status_ref": rdb_status_ref,
            "selected_next_stage_candidate_ref": candidate_ref,
            "selected_next_stage_candidate_kind_ref": candidate_kind_ref,
            "rdb_op08_next_required_step_ref": candidate_ref,
            "decision_lane_ref": decision_lane_ref,
            "manual_decision_material_ref": f"nci_op06_op07_fixture_{decision_lane_ref}",
            "manual_decision_material_kind_ref": decision_lane_ref,
            "manual_decision_material_present": True,
        }
    )
    return op01


def _op02_from_op05(op05: dict[str, object]) -> dict[str, object]:
    return nci.build_p7_r54_ahr_post_rdb08_nci_op02_selected_next_stage_candidate_shape_validation(
        _op01_from_op05(op05),
    )


def _op03_from_op05(op05: dict[str, object]) -> dict[str, object]:
    return nci.build_p7_r54_ahr_post_rdb08_nci_op03_selected_candidate_lane_consistency_resolver(
        _op02_from_op05(op05),
    )


def _op03_with_selected_candidate_shape(
    *,
    rdb_status_ref: str,
    candidate_ref: str,
    candidate_kind_ref: str,
    decision_lane_ref: str,
) -> dict[str, object]:
    return nci.build_p7_r54_ahr_post_rdb08_nci_op03_selected_candidate_lane_consistency_resolver(
        nci.build_p7_r54_ahr_post_rdb08_nci_op02_selected_next_stage_candidate_shape_validation(
            _op01_with_selected_candidate_shape(
                rdb_status_ref=rdb_status_ref,
                candidate_ref=candidate_ref,
                candidate_kind_ref=candidate_kind_ref,
                decision_lane_ref=decision_lane_ref,
            )
        )
    )


def _op04_from_op05(op05: dict[str, object]) -> dict[str, object]:
    return nci.build_p7_r54_ahr_post_rdb08_nci_op04_next_design_target_or_stop_materialization(
        _op03_from_op05(op05),
    )


def _op05_guard_from_op05(op05: dict[str, object]) -> dict[str, object]:
    return nci.build_p7_r54_ahr_post_rdb08_nci_op05_bodyfree_no_touch_no_promotion_no_auto_execution_guard(
        _op04_from_op05(op05),
    )


def _op05_guard_from_op03(op03: dict[str, object]) -> dict[str, object]:
    return nci.build_p7_r54_ahr_post_rdb08_nci_op05_bodyfree_no_touch_no_promotion_no_auto_execution_guard(
        nci.build_p7_r54_ahr_post_rdb08_nci_op04_next_design_target_or_stop_materialization(op03),
    )


def _op06_from_op05_guard(op05_guard: dict[str, object]) -> dict[str, object]:
    return nci.build_p7_r54_ahr_post_rdb08_nci_op06_selected_regression_compileall_validation_plan(op05_guard)


def _valid_handoff_guard_materials() -> list[tuple[dict[str, object], str, str]]:
    return [
        (_op05_guard_from_op05(_op05_confirmed()), nci.P7_R54_AHR_POST_RDB08_NCI_LANE_DHR_OP05_DESIGN_TARGET_REF, nci.P7_R54_AHR_POST_RDB08_NCI_NEXT_DESIGN_DHR_OP05_BOUNDARY_REF),
        (_op05_guard_from_op05(_op05_not_confirmed()), nci.P7_R54_AHR_POST_RDB08_NCI_LANE_RETRY_OR_START_ROUTE_REF, nci.P7_R54_AHR_POST_RDB08_NCI_NEXT_DESIGN_RETRY_OR_START_REF),
        (_op05_guard_from_op05(_op05_waiting_result()), nci.P7_R54_AHR_POST_RDB08_NCI_LANE_WAIT_EXTERNAL_BODYFREE_CLAIM_REF, nci.P7_R54_AHR_POST_RDB08_NCI_NEXT_DESIGN_WAIT_EXTERNAL_CLAIM_REF),
        (_op05_guard_from_op05(_op05_invalid_result()), nci.P7_R54_AHR_POST_RDB08_NCI_LANE_REPAIR_RDB_OR_UPSTREAM_RESULT_REF, nci.P7_R54_AHR_POST_RDB08_NCI_NEXT_DESIGN_REPAIR_BOUNDARY_REF),
    ]


def _valid_stop_guard_materials() -> list[tuple[dict[str, object], str, str]]:
    unresolved_op03 = _op03_with_selected_candidate_shape(
        rdb_status_ref=rdb.P7_R54_AHR_POST_MRB08_RDB_STATUS_INCOMPLETE_UNRESOLVED_MANUAL_HOLD_STOPPED_REF,
        candidate_ref=rdb.P7_R54_AHR_POST_MRB08_RDB_NEXT_STEP_MANUAL_HOLD_UNRESOLVED_REF,
        candidate_kind_ref=rdb.P7_R54_AHR_POST_MRB08_RDB_CANDIDATE_KIND_UNRESOLVED_REF,
        decision_lane_ref=rdb.P7_R54_AHR_POST_MRB08_RDB_DECISION_LANE_MANUAL_HOLD_UNRESOLVED_REF,
    )
    blocked_op03 = _op03_with_selected_candidate_shape(
        rdb_status_ref=rdb.P7_R54_AHR_POST_MRB08_RDB_STATUS_BLOCKED_BODYFREE_LEAK_PROMOTION_OR_AUTORUN_REF,
        candidate_ref=rdb.P7_R54_AHR_POST_MRB08_RDB_NEXT_STEP_BLOCKED_POST_MRB08_REF,
        candidate_kind_ref=rdb.P7_R54_AHR_POST_MRB08_RDB_CANDIDATE_KIND_BLOCKED_REF,
        decision_lane_ref=rdb.P7_R54_AHR_POST_MRB08_RDB_DECISION_LANE_BLOCKED_REF,
    )
    return [
        (_op05_guard_from_op03(unresolved_op03), nci.P7_R54_AHR_POST_RDB08_NCI_LANE_MANUAL_HOLD_UNRESOLVED_REF, nci.P7_R54_AHR_POST_RDB08_NCI_NEXT_STOP_MANUAL_HOLD_REF),
        (_op05_guard_from_op03(blocked_op03), nci.P7_R54_AHR_POST_RDB08_NCI_LANE_BLOCKED_BODYFREE_PROMOTION_AUTORUN_REF, nci.P7_R54_AHR_POST_RDB08_NCI_NEXT_STOP_BLOCKED_REF),
    ]


def test_nci_op06_records_validation_plan_refs_without_executing_tests_or_claiming_green() -> None:
    material = nci.build_p7_r54_ahr_post_rdb08_nci_op06_selected_regression_compileall_validation_plan(
        _op05_guard_from_op05(_op05_confirmed())
    )

    assert set(material) == set(nci.P7_R54_AHR_POST_RDB08_NCI_OP06_REQUIRED_FIELD_REFS)
    assert material["schema_version"] == nci.P7_R54_AHR_POST_RDB08_NCI_OP06_SCHEMA_VERSION
    assert material["operation_step_ref"] == nci.P7_R54_AHR_POST_RDB08_NCI_OP06_STEP_REF
    assert material["op05_contract_valid"] is True
    assert material["op05_guard_passed"] is True
    assert material["nci_op06_validation_plan_status_ref"] == nci.P7_R54_AHR_POST_RDB08_NCI_OP06_STATUS_VALIDATION_PLAN_RECORDED_REF
    assert material["target_test_refs"] == list(nci.P7_R54_AHR_POST_RDB08_NCI_TARGET_TEST_REF_REFS)
    assert material["selected_regression_test_refs"] == list(nci.P7_R54_AHR_POST_RDB08_NCI_SELECTED_REGRESSION_TEST_REF_REFS)
    assert material["compileall_target_refs"] == list(nci.P7_R54_AHR_POST_RDB08_NCI_COMPILEALL_TARGET_REF_REFS)
    assert material["validation_command_summary_refs"] == list(nci.P7_R54_AHR_POST_RDB08_NCI_VALIDATION_COMMAND_SUMMARY_REFS)
    assert material["target_tests_planned"] is True
    assert material["selected_regression_planned"] is True
    assert material["compileall_planned"] is True
    assert material["op06_validation_plan_recorded"] is True
    assert material["op06_does_not_execute_validation_commands"] is True
    assert material["full_backend_suite_green_claimed_here"] is False
    assert material["rn_contract_green_claimed_here"] is False
    assert material["actual_review_execution_confirmed"] is False
    assert material["nci_op06_blocker_refs"] == []
    assert material["next_required_step"] == nci.P7_R54_AHR_POST_RDB08_NCI_OP07_STEP_REF
    for key in TRUE_BOUNDARY_KEYS_OP06:
        assert material[key] is True, key
    assert nci.assert_p7_r54_ahr_post_rdb08_nci_op06_selected_regression_compileall_validation_plan_contract(material) is True
    _assert_common_bodyfree_no_touch_no_promotion(material)


@pytest.mark.parametrize(("op05_guard", "expected_lane", "expected_ref"), _valid_handoff_guard_materials() + _valid_stop_guard_materials())
def test_nci_op06_carries_selected_lane_into_validation_plan_without_promotion(
    op05_guard: dict[str, object],
    expected_lane: str,
    expected_ref: str,
) -> None:
    material = _op06_from_op05_guard(op05_guard)

    assert material["nci_op06_validation_plan_status_ref"] == nci.P7_R54_AHR_POST_RDB08_NCI_OP06_STATUS_VALIDATION_PLAN_RECORDED_REF
    assert material["selected_nci_lane_ref"] == expected_lane
    assert material["selected_next_design_target_or_stop_ref"] == expected_ref
    assert material["selected_next_design_target_or_stop_not_executed"] is True
    assert material["p8_start_allowed"] is False
    assert material["release_allowed"] is False
    assert nci.assert_p7_r54_ahr_post_rdb08_nci_op06_selected_regression_compileall_validation_plan_contract(material) is True
    _assert_common_bodyfree_no_touch_no_promotion(material)


def test_nci_op06_waits_when_op05_guard_is_valid_but_not_passed() -> None:
    op04 = _op04_from_op05(_op05_confirmed())
    op04["dhr_op05_called_here"] = True
    op05_guard = nci.build_p7_r54_ahr_post_rdb08_nci_op05_bodyfree_no_touch_no_promotion_no_auto_execution_guard(op04)
    assert op05_guard["nci_op05_guard_status_ref"] == nci.P7_R54_AHR_POST_RDB08_NCI_OP05_STATUS_BLOCKED_BODYFREE_PROMOTION_AUTORUN_REF

    material = _op06_from_op05_guard(op05_guard)

    assert material["op05_contract_valid"] is True
    assert material["op05_guard_passed"] is False
    assert material["nci_op06_validation_plan_status_ref"] == nci.P7_R54_AHR_POST_RDB08_NCI_OP06_STATUS_WAITING_FOR_OP05_GUARD_REF
    assert material["op06_validation_plan_recorded"] is False
    assert material["nci_op06_blocker_refs"] == ["nci_op05_guard_not_passed"]
    assert material["next_required_step"] == nci.P7_R54_AHR_POST_RDB08_NCI_NEXT_STEP_WAIT_FOR_OP05_GUARD_REF
    assert nci.assert_p7_r54_ahr_post_rdb08_nci_op06_selected_regression_compileall_validation_plan_contract(material) is True
    _assert_common_bodyfree_no_touch_no_promotion(material)


def test_nci_op06_repairs_invalid_op05_contract_without_executing_repair() -> None:
    op05_guard = _op05_guard_from_op05(_op05_confirmed())
    op05_guard["next_required_step"] = nci.P7_R54_AHR_POST_RDB08_NCI_NEXT_DESIGN_DHR_OP05_BOUNDARY_REF

    material = _op06_from_op05_guard(op05_guard)

    assert material["op05_contract_valid"] is False
    assert material["nci_op06_validation_plan_status_ref"] == nci.P7_R54_AHR_POST_RDB08_NCI_OP06_STATUS_REPAIR_REQUIRED_REF
    assert material["op06_validation_plan_recorded"] is False
    assert material["nci_op06_blocker_refs"] == ["nci_op05_contract_invalid"]
    assert material["next_required_step"] == nci.P7_R54_AHR_POST_RDB08_NCI_NEXT_STEP_REPAIR_OP06_VALIDATION_PLAN_REF
    assert material["actual_review_execution_confirmed"] is False
    assert nci.assert_p7_r54_ahr_post_rdb08_nci_op06_selected_regression_compileall_validation_plan_contract(material) is True
    _assert_common_bodyfree_no_touch_no_promotion(material)


@pytest.mark.parametrize(
    ("mutation", "evidence_field", "expected_blocker"),
    [
        ({"question_text": "must be blocked"}, "op06_input_forbidden_payload_key_path_refs", "op05_input_forbidden_payload_key_detected"),
        ({"stdout_body": "must be blocked"}, "op06_input_body_like_value_path_refs", "op05_input_body_like_value_detected"),
        ({"dhr_op05_called_here": True}, "op06_input_promotion_claim_refs", "op05_input_promotion_or_autorun_claim_detected"),
        ({"modified_file_refs": ["api/routes/emlis.py"]}, "op06_input_no_touch_mutation_path_refs", "op05_input_api_db_rn_runtime_response_key_or_p8_question_touch_detected"),
    ],
)
def test_nci_op06_blocks_bodyfree_no_touch_promotion_or_autorun_claims(
    mutation: dict[str, object],
    evidence_field: str,
    expected_blocker: str,
) -> None:
    op05_guard = _op05_guard_from_op05(_op05_confirmed())
    op05_guard.update(mutation)

    material = _op06_from_op05_guard(op05_guard)

    assert material["nci_op06_validation_plan_status_ref"] == nci.P7_R54_AHR_POST_RDB08_NCI_OP06_STATUS_BLOCKED_BODYFREE_PROMOTION_AUTORUN_REF
    assert material["op06_validation_plan_recorded"] is False
    assert material[evidence_field]
    assert expected_blocker in material["nci_op06_blocker_refs"]
    assert material["next_required_step"] == nci.P7_R54_AHR_POST_RDB08_NCI_NEXT_STEP_BLOCKED_OP06_VALIDATION_PLAN_REF
    assert nci.assert_p7_r54_ahr_post_rdb08_nci_op06_selected_regression_compileall_validation_plan_contract(material) is True
    _assert_common_bodyfree_no_touch_no_promotion(material)


@pytest.mark.parametrize(("op05_guard", "expected_lane", "expected_ref"), _valid_handoff_guard_materials())
def test_nci_op07_drafts_handoff_envelope_for_handoff_lanes_without_executing(
    op05_guard: dict[str, object],
    expected_lane: str,
    expected_ref: str,
) -> None:
    op06 = _op06_from_op05_guard(op05_guard)
    material = nci.build_p7_r54_ahr_post_rdb08_nci_op07_handoff_or_stop_envelope_draft_material(op06)

    assert set(material) == set(nci.P7_R54_AHR_POST_RDB08_NCI_OP07_REQUIRED_FIELD_REFS)
    assert material["schema_version"] == nci.P7_R54_AHR_POST_RDB08_NCI_OP07_SCHEMA_VERSION
    assert material["operation_step_ref"] == nci.P7_R54_AHR_POST_RDB08_NCI_OP07_STEP_REF
    assert material["op06_contract_valid"] is True
    assert material["op06_validation_plan_recorded"] is True
    assert material["nci_op07_status_ref"] == nci.P7_R54_AHR_POST_RDB08_NCI_OP07_STATUS_HANDOFF_ENVELOPE_DRAFT_REF
    assert material["handoff_or_stop_envelope_kind_ref"] == nci.P7_R54_AHR_POST_RDB08_NCI_OP07_HANDOFF_ENVELOPE_KIND_REF
    assert material["handoff_or_stop_envelope_bodyfree"] is True
    assert material["handoff_envelope_present"] is True
    assert material["stop_envelope_present"] is False
    assert material["selected_nci_lane_ref"] == expected_lane
    assert material["selected_next_design_or_stop_ref"] == expected_ref
    assert material["selected_next_design_or_stop_not_executed"] is True
    assert material["nci_op07_ready_for_op08"] is True
    assert material["nci_op07_blocker_refs"] == []
    assert material["next_required_step"] == nci.P7_R54_AHR_POST_RDB08_NCI_OP08_STEP_REF
    assert sum(1 for key in LANE_FLAG_KEYS if material[key] is True) == 1
    for key in TRUE_BOUNDARY_KEYS_OP07:
        assert material[key] is True, key
    _assert_no_downstream_execution(material)
    assert nci.assert_p7_r54_ahr_post_rdb08_nci_op07_handoff_or_stop_envelope_draft_material_contract(material) is True
    _assert_common_bodyfree_no_touch_no_promotion(material)


@pytest.mark.parametrize(("op05_guard", "expected_lane", "expected_ref"), _valid_stop_guard_materials())
def test_nci_op07_drafts_stop_envelope_for_unresolved_or_blocked_lanes_without_promotion(
    op05_guard: dict[str, object],
    expected_lane: str,
    expected_ref: str,
) -> None:
    op06 = _op06_from_op05_guard(op05_guard)
    material = nci.build_p7_r54_ahr_post_rdb08_nci_op07_handoff_or_stop_envelope_draft_material(op06)

    assert material["op06_contract_valid"] is True
    assert material["op06_validation_plan_recorded"] is True
    assert material["nci_op07_status_ref"] == nci.P7_R54_AHR_POST_RDB08_NCI_OP07_STATUS_STOP_ENVELOPE_DRAFT_REF
    assert material["handoff_or_stop_envelope_kind_ref"] == nci.P7_R54_AHR_POST_RDB08_NCI_OP07_STOP_ENVELOPE_KIND_REF
    assert material["handoff_envelope_present"] is False
    assert material["stop_envelope_present"] is True
    assert material["selected_nci_lane_ref"] == expected_lane
    assert material["selected_next_design_or_stop_ref"] == expected_ref
    assert material["selected_next_design_or_stop_not_executed"] is True
    assert material["nci_op07_ready_for_op08"] is True
    assert material["next_required_step"] == nci.P7_R54_AHR_POST_RDB08_NCI_OP08_STEP_REF
    _assert_no_downstream_execution(material)
    assert nci.assert_p7_r54_ahr_post_rdb08_nci_op07_handoff_or_stop_envelope_draft_material_contract(material) is True
    _assert_common_bodyfree_no_touch_no_promotion(material)


def test_nci_op07_drafts_stop_envelope_when_op06_validation_plan_is_invalid() -> None:
    op06 = _op06_from_op05_guard(_op05_guard_from_op05(_op05_confirmed()))
    op06["target_test_ref_count"] = 0

    material = nci.build_p7_r54_ahr_post_rdb08_nci_op07_handoff_or_stop_envelope_draft_material(op06)

    assert material["op06_contract_valid"] is False
    assert material["nci_op07_status_ref"] == nci.P7_R54_AHR_POST_RDB08_NCI_OP07_STATUS_STOP_ENVELOPE_DRAFT_REF
    assert material["handoff_envelope_present"] is False
    assert material["stop_envelope_present"] is True
    assert material["nci_op07_ready_for_op08"] is True
    assert material["nci_op07_blocker_refs"] == ["nci_op06_contract_invalid"]
    assert material["next_required_step"] == nci.P7_R54_AHR_POST_RDB08_NCI_OP08_STEP_REF
    assert nci.assert_p7_r54_ahr_post_rdb08_nci_op07_handoff_or_stop_envelope_draft_material_contract(material) is True
    _assert_common_bodyfree_no_touch_no_promotion(material)


def test_nci_op07_drafts_stop_envelope_when_op06_is_waiting_for_op05_guard() -> None:
    op04 = _op04_from_op05(_op05_confirmed())
    op04["dhr_op05_called_here"] = True
    op05_guard = nci.build_p7_r54_ahr_post_rdb08_nci_op05_bodyfree_no_touch_no_promotion_no_auto_execution_guard(op04)
    op06 = _op06_from_op05_guard(op05_guard)

    material = nci.build_p7_r54_ahr_post_rdb08_nci_op07_handoff_or_stop_envelope_draft_material(op06)

    assert material["op06_contract_valid"] is True
    assert material["op06_validation_plan_recorded"] is False
    assert material["op05_guard_passed"] is False
    assert material["nci_op07_status_ref"] == nci.P7_R54_AHR_POST_RDB08_NCI_OP07_STATUS_STOP_ENVELOPE_DRAFT_REF
    assert material["handoff_envelope_present"] is False
    assert material["stop_envelope_present"] is True
    assert material["nci_op07_ready_for_op08"] is True
    assert "nci_op06_validation_plan_not_recorded_or_op05_guard_not_passed" in material["nci_op07_blocker_refs"]
    assert nci.assert_p7_r54_ahr_post_rdb08_nci_op07_handoff_or_stop_envelope_draft_material_contract(material) is True
    _assert_common_bodyfree_no_touch_no_promotion(material)


@pytest.mark.parametrize(
    ("mutation", "evidence_field", "expected_blocker"),
    [
        ({"question_text": "must be blocked"}, "op07_input_forbidden_payload_key_path_refs", "op06_input_forbidden_payload_key_detected"),
        ({"stderr_body": "must be blocked"}, "op07_input_body_like_value_path_refs", "op06_input_body_like_value_detected"),
        ({"dhr_op05_called_here": True}, "op07_input_promotion_claim_refs", "op06_input_promotion_or_autorun_claim_detected"),
        ({"changed_file_refs": ["Cocolon/tests/rn-screen-contracts.test.js"]}, "op07_input_no_touch_mutation_path_refs", "op06_input_api_db_rn_runtime_response_key_or_p8_question_touch_detected"),
    ],
)
def test_nci_op07_blocks_bodyfree_no_touch_promotion_or_autorun_claims(
    mutation: dict[str, object],
    evidence_field: str,
    expected_blocker: str,
) -> None:
    op06 = _op06_from_op05_guard(_op05_guard_from_op05(_op05_confirmed()))
    op06.update(mutation)

    material = nci.build_p7_r54_ahr_post_rdb08_nci_op07_handoff_or_stop_envelope_draft_material(op06)

    assert material["nci_op07_status_ref"] == nci.P7_R54_AHR_POST_RDB08_NCI_OP07_STATUS_BLOCKED_BODYFREE_PROMOTION_AUTORUN_REF
    assert material["handoff_envelope_present"] is False
    assert material["stop_envelope_present"] is True
    assert material["nci_op07_ready_for_op08"] is False
    assert material[evidence_field]
    assert expected_blocker in material["nci_op07_blocker_refs"]
    assert material["next_required_step"] == nci.P7_R54_AHR_POST_RDB08_NCI_NEXT_STEP_BLOCKED_OP07_ENVELOPE_REF
    assert nci.assert_p7_r54_ahr_post_rdb08_nci_op07_handoff_or_stop_envelope_draft_material_contract(material) is True
    _assert_common_bodyfree_no_touch_no_promotion(material)


@pytest.mark.parametrize(
    ("builder", "assertor", "material", "field", "bad_value"),
    [
        (
            nci.build_p7_r54_ahr_post_rdb08_nci_op06_selected_regression_compileall_validation_plan,
            nci.assert_p7_r54_ahr_post_rdb08_nci_op06_selected_regression_compileall_validation_plan_contract,
            _op05_guard_from_op05(_op05_confirmed()),
            "full_backend_suite_green_claimed_here",
            True,
        ),
        (
            nci.build_p7_r54_ahr_post_rdb08_nci_op07_handoff_or_stop_envelope_draft_material,
            nci.assert_p7_r54_ahr_post_rdb08_nci_op07_handoff_or_stop_envelope_draft_material_contract,
            _op06_from_op05_guard(_op05_guard_from_op05(_op05_confirmed())),
            "dhr_op05_builder_called_here",
            True,
        ),
        (
            nci.build_p7_r54_ahr_post_rdb08_nci_op07_handoff_or_stop_envelope_draft_material,
            nci.assert_p7_r54_ahr_post_rdb08_nci_op07_handoff_or_stop_envelope_draft_material_contract,
            _op06_from_op05_guard(_op05_guard_from_op05(_op05_confirmed())),
            "p8_question_substitution_allowed",
            True,
        ),
    ],
)
def test_nci_op06_op07_contracts_reject_execution_p8_or_green_claim_mutations(
    builder,
    assertor,
    material: dict[str, object],
    field: str,
    bad_value: object,
) -> None:
    built = builder(material)
    built[field] = bad_value

    with pytest.raises(ValueError):
        assertor(built)


def test_nci_op06_op07_full_title_aliases_match_short_builders_and_asserts() -> None:
    op05_guard = _op05_guard_from_op05(_op05_confirmed())
    op06_short = nci.build_p7_r54_ahr_post_rdb08_nci_op06_selected_regression_compileall_validation_plan(op05_guard)
    op06_alias = nci.build_p7_r54_ahr_post_rdb08_selected_next_stage_candidate_intake_nci_op06_selected_regression_compileall_validation_plan(op05_guard)
    assert op06_alias == op06_short
    assert nci.assert_p7_r54_ahr_post_rdb08_selected_next_stage_candidate_intake_nci_op06_selected_regression_compileall_validation_plan_contract(op06_alias) is True

    op07_short = nci.build_p7_r54_ahr_post_rdb08_nci_op07_handoff_or_stop_envelope_draft_material(op06_short)
    op07_alias = nci.build_p7_r54_ahr_post_rdb08_selected_next_stage_candidate_intake_nci_op07_handoff_or_stop_envelope_draft_material(op06_short)
    assert op07_alias == op07_short
    assert nci.assert_p7_r54_ahr_post_rdb08_selected_next_stage_candidate_intake_nci_op07_handoff_or_stop_envelope_draft_material_contract(op07_alias) is True
