# -*- coding: utf-8 -*-
"""R54-AHR Post-RDB08 selected next-stage candidate intake NCI-OP04/OP05 tests."""

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


TRUE_BOUNDARY_KEYS_OP04 = (
    "nci_op04_does_not_execute_selected_next_stage_candidate",
    "nci_op04_does_not_call_dhr_op05",
    "nci_op04_does_not_start_actual_review",
    "nci_op04_does_not_request_raw_evidence",
    "nci_op04_does_not_execute_repair",
    "nci_op04_does_not_start_p8_question_design",
    "nci_op04_does_not_change_api_db_rn_runtime_response_key",
)

TRUE_BOUNDARY_KEYS_OP05 = (
    "nci_op05_does_not_execute_selected_next_stage_candidate",
    "nci_op05_does_not_call_dhr_op05",
    "nci_op05_does_not_start_actual_review",
    "nci_op05_does_not_request_raw_evidence",
    "nci_op05_does_not_execute_repair",
    "nci_op05_does_not_start_p8_question_design",
    "nci_op05_does_not_change_api_db_rn_runtime_response_key",
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


def _op01_from_op05(op05: dict[str, object]) -> dict[str, object]:
    return nci.build_p7_r54_ahr_post_rdb08_nci_op01_rdb_op08_bodyfree_result_memo_closure_intake(
        rdb_op08_bodyfree_result_memo_closure=_op08_from_op05(op05),
    )


def _op02_from_op05(op05: dict[str, object]) -> dict[str, object]:
    return nci.build_p7_r54_ahr_post_rdb08_nci_op02_selected_next_stage_candidate_shape_validation(
        _op01_from_op05(op05),
    )


def _op03_from_op05(op05: dict[str, object]) -> dict[str, object]:
    return nci.build_p7_r54_ahr_post_rdb08_nci_op03_selected_candidate_lane_consistency_resolver(
        _op02_from_op05(op05),
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
            "manual_decision_material_ref": f"nci_op04_op05_fixture_{decision_lane_ref}",
            "manual_decision_material_kind_ref": decision_lane_ref,
            "manual_decision_material_present": True,
        }
    )
    return op01


def _op03_with_selected_candidate_shape(
    *,
    rdb_status_ref: str,
    candidate_ref: str,
    candidate_kind_ref: str,
    decision_lane_ref: str,
) -> dict[str, object]:
    op01 = _op01_with_selected_candidate_shape(
        rdb_status_ref=rdb_status_ref,
        candidate_ref=candidate_ref,
        candidate_kind_ref=candidate_kind_ref,
        decision_lane_ref=decision_lane_ref,
    )
    op02 = nci.build_p7_r54_ahr_post_rdb08_nci_op02_selected_next_stage_candidate_shape_validation(op01)
    return nci.build_p7_r54_ahr_post_rdb08_nci_op03_selected_candidate_lane_consistency_resolver(op02)


def _op04_from_op05(op05: dict[str, object]) -> dict[str, object]:
    return nci.build_p7_r54_ahr_post_rdb08_nci_op04_next_design_target_or_stop_materialization(
        _op03_from_op05(op05),
    )


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


@pytest.mark.parametrize(
    ("op05", "expected_lane", "expected_next_ref", "expected_presence_key"),
    [
        (
            _op05_confirmed(),
            nci.P7_R54_AHR_POST_RDB08_NCI_LANE_DHR_OP05_DESIGN_TARGET_REF,
            nci.P7_R54_AHR_POST_RDB08_NCI_NEXT_DESIGN_DHR_OP05_BOUNDARY_REF,
            "dhr_op05_design_target_candidate_present",
        ),
        (
            _op05_not_confirmed(),
            nci.P7_R54_AHR_POST_RDB08_NCI_LANE_RETRY_OR_START_ROUTE_REF,
            nci.P7_R54_AHR_POST_RDB08_NCI_NEXT_DESIGN_RETRY_OR_START_REF,
            "retry_or_start_route_candidate_present",
        ),
        (
            _op05_waiting_result(),
            nci.P7_R54_AHR_POST_RDB08_NCI_LANE_WAIT_EXTERNAL_BODYFREE_CLAIM_REF,
            nci.P7_R54_AHR_POST_RDB08_NCI_NEXT_DESIGN_WAIT_EXTERNAL_CLAIM_REF,
            "external_claim_wait_candidate_present",
        ),
        (
            _op05_invalid_result(),
            nci.P7_R54_AHR_POST_RDB08_NCI_LANE_REPAIR_RDB_OR_UPSTREAM_RESULT_REF,
            nci.P7_R54_AHR_POST_RDB08_NCI_NEXT_DESIGN_REPAIR_BOUNDARY_REF,
            "repair_route_candidate_present",
        ),
    ],
)
def test_nci_op04_materializes_next_design_targets_without_executing_selected_candidate(
    op05: dict[str, object],
    expected_lane: str,
    expected_next_ref: str,
    expected_presence_key: str,
) -> None:
    op03 = _op03_from_op05(op05)
    material = nci.build_p7_r54_ahr_post_rdb08_nci_op04_next_design_target_or_stop_materialization(op03)

    assert set(material) == set(nci.P7_R54_AHR_POST_RDB08_NCI_OP04_REQUIRED_FIELD_REFS)
    assert material["schema_version"] == nci.P7_R54_AHR_POST_RDB08_NCI_OP04_SCHEMA_VERSION
    assert material["operation_step_ref"] == nci.P7_R54_AHR_POST_RDB08_NCI_OP04_STEP_REF
    assert material["op03_contract_valid"] is True
    assert material["op03_candidate_lane_consistent"] is True
    assert material["op03_exactly_one_nci_lane_selected"] is True
    assert material["nci_lane_ref"] == expected_lane
    assert material["nci_op04_status_ref"] == nci.P7_R54_AHR_POST_RDB08_NCI_OP04_STATUS_NEXT_DESIGN_TARGET_MATERIALIZED_REF
    assert material["next_design_target_or_stop_ref"] == expected_next_ref
    assert material["next_design_target_or_stop_not_executed"] is True
    assert material["next_design_target_materialized"] is True
    assert material["stop_materialized"] is False
    assert material["handoff_candidate_materialized"] is True
    assert material["stop_candidate_materialized"] is False
    assert material[expected_presence_key] is True
    assert sum(1 for key in LANE_FLAG_KEYS if material[key] is True) == 1
    assert material["nci_op04_blocker_refs"] == []
    assert material["next_required_step"] == nci.P7_R54_AHR_POST_RDB08_NCI_OP05_STEP_REF
    for key in TRUE_BOUNDARY_KEYS_OP04:
        assert material[key] is True, key
    _assert_no_downstream_execution(material)
    assert nci.assert_p7_r54_ahr_post_rdb08_nci_op04_next_design_target_or_stop_materialization_contract(material) is True
    _assert_common_bodyfree_no_touch_no_promotion(material)


@pytest.mark.parametrize(
    ("op03", "expected_next_ref", "expected_presence_key"),
    [
        (
            _op03_with_selected_candidate_shape(
                rdb_status_ref=rdb.P7_R54_AHR_POST_MRB08_RDB_STATUS_INCOMPLETE_UNRESOLVED_MANUAL_HOLD_STOPPED_REF,
                candidate_ref=rdb.P7_R54_AHR_POST_MRB08_RDB_NEXT_STEP_MANUAL_HOLD_UNRESOLVED_REF,
                candidate_kind_ref=rdb.P7_R54_AHR_POST_MRB08_RDB_CANDIDATE_KIND_UNRESOLVED_REF,
                decision_lane_ref=rdb.P7_R54_AHR_POST_MRB08_RDB_DECISION_LANE_MANUAL_HOLD_UNRESOLVED_REF,
            ),
            nci.P7_R54_AHR_POST_RDB08_NCI_NEXT_STOP_MANUAL_HOLD_REF,
            "unresolved_manual_hold_candidate_present",
        ),
        (
            _op03_with_selected_candidate_shape(
                rdb_status_ref=rdb.P7_R54_AHR_POST_MRB08_RDB_STATUS_BLOCKED_BODYFREE_LEAK_PROMOTION_OR_AUTORUN_REF,
                candidate_ref=rdb.P7_R54_AHR_POST_MRB08_RDB_NEXT_STEP_BLOCKED_POST_MRB08_REF,
                candidate_kind_ref=rdb.P7_R54_AHR_POST_MRB08_RDB_CANDIDATE_KIND_BLOCKED_REF,
                decision_lane_ref=rdb.P7_R54_AHR_POST_MRB08_RDB_DECISION_LANE_BLOCKED_REF,
            ),
            nci.P7_R54_AHR_POST_RDB08_NCI_NEXT_STOP_BLOCKED_REF,
            "blocked_candidate_present",
        ),
    ],
)
def test_nci_op04_materializes_unresolved_or_blocked_as_stop_without_promotion(
    op03: dict[str, object],
    expected_next_ref: str,
    expected_presence_key: str,
) -> None:
    material = nci.build_p7_r54_ahr_post_rdb08_nci_op04_next_design_target_or_stop_materialization(op03)

    assert material["nci_op04_status_ref"] == nci.P7_R54_AHR_POST_RDB08_NCI_OP04_STATUS_STOP_MATERIALIZED_REF
    assert material["next_design_target_or_stop_ref"] == expected_next_ref
    assert material["next_design_target_or_stop_not_executed"] is True
    assert material["next_design_target_materialized"] is False
    assert material["stop_materialized"] is True
    assert material["handoff_candidate_materialized"] is False
    assert material["stop_candidate_materialized"] is True
    assert material[expected_presence_key] is True
    assert sum(1 for key in LANE_FLAG_KEYS if material[key] is True) == 1
    assert material["nci_op04_blocker_refs"] == []
    assert material["next_required_step"] == nci.P7_R54_AHR_POST_RDB08_NCI_OP05_STEP_REF
    _assert_no_downstream_execution(material)
    assert nci.assert_p7_r54_ahr_post_rdb08_nci_op04_next_design_target_or_stop_materialization_contract(material) is True
    _assert_common_bodyfree_no_touch_no_promotion(material)


@pytest.mark.parametrize(
    ("mutation", "evidence_field", "expected_blocker"),
    [
        ({"question_text": "must be blocked"}, "op04_input_forbidden_payload_key_path_refs", "op03_input_forbidden_payload_key_detected"),
        ({"stdout_body": "must be blocked"}, "op04_input_body_like_value_path_refs", "op03_input_body_like_value_detected"),
        ({"dhr_op05_called_here": True}, "op04_input_promotion_claim_refs", "op03_input_promotion_or_autorun_claim_detected"),
    ],
)
def test_nci_op04_blocks_bodyfree_leak_or_promotion_before_materialization_guard(
    mutation: dict[str, object],
    evidence_field: str,
    expected_blocker: str,
) -> None:
    op03 = _op03_from_op05(_op05_confirmed())
    op03.update(mutation)

    material = nci.build_p7_r54_ahr_post_rdb08_nci_op04_next_design_target_or_stop_materialization(op03)

    assert material["nci_op04_status_ref"] == nci.P7_R54_AHR_POST_RDB08_NCI_OP04_STATUS_BLOCKED_BODYFREE_PROMOTION_AUTORUN_REF
    assert material["next_design_target_or_stop_not_executed"] is False
    assert material["next_design_target_materialized"] is False
    assert material["stop_materialized"] is False
    assert material[evidence_field]
    assert expected_blocker in material["nci_op04_blocker_refs"]
    assert material["next_required_step"] == nci.P7_R54_AHR_POST_RDB08_NCI_NEXT_STEP_BLOCKED_OP04_MATERIALIZATION_REF
    _assert_no_downstream_execution(material)
    assert nci.assert_p7_r54_ahr_post_rdb08_nci_op04_next_design_target_or_stop_materialization_contract(material) is True
    _assert_common_bodyfree_no_touch_no_promotion(material)


def test_nci_op04_repairs_invalid_op03_contract_without_executing_repair() -> None:
    op03 = _op03_from_op05(_op05_confirmed())
    op03["next_required_step"] = nci.P7_R54_AHR_POST_RDB08_NCI_NEXT_DESIGN_DHR_OP05_BOUNDARY_REF

    material = nci.build_p7_r54_ahr_post_rdb08_nci_op04_next_design_target_or_stop_materialization(op03)

    assert material["nci_op04_status_ref"] == nci.P7_R54_AHR_POST_RDB08_NCI_OP04_STATUS_REPAIR_REQUIRED_REF
    assert material["op03_contract_valid"] is False
    assert material["next_design_target_or_stop_not_executed"] is False
    assert material["nci_op04_blocker_refs"] == ["nci_op03_contract_invalid"]
    assert material["repair_executed_here"] is False
    assert material["next_required_step"] == nci.P7_R54_AHR_POST_RDB08_NCI_NEXT_STEP_REPAIR_OP04_MATERIALIZATION_REF
    assert nci.assert_p7_r54_ahr_post_rdb08_nci_op04_next_design_target_or_stop_materialization_contract(material) is True
    _assert_common_bodyfree_no_touch_no_promotion(material)


@pytest.mark.parametrize(
    ("op04"),
    [
        _op04_from_op05(_op05_confirmed()),
        _op04_from_op05(_op05_not_confirmed()),
        _op04_from_op05(_op05_waiting_result()),
        _op04_from_op05(_op05_invalid_result()),
        nci.build_p7_r54_ahr_post_rdb08_nci_op04_next_design_target_or_stop_materialization(
            _op03_with_selected_candidate_shape(
                rdb_status_ref=rdb.P7_R54_AHR_POST_MRB08_RDB_STATUS_INCOMPLETE_UNRESOLVED_MANUAL_HOLD_STOPPED_REF,
                candidate_ref=rdb.P7_R54_AHR_POST_MRB08_RDB_NEXT_STEP_MANUAL_HOLD_UNRESOLVED_REF,
                candidate_kind_ref=rdb.P7_R54_AHR_POST_MRB08_RDB_CANDIDATE_KIND_UNRESOLVED_REF,
                decision_lane_ref=rdb.P7_R54_AHR_POST_MRB08_RDB_DECISION_LANE_MANUAL_HOLD_UNRESOLVED_REF,
            ),
        ),
        nci.build_p7_r54_ahr_post_rdb08_nci_op04_next_design_target_or_stop_materialization(
            _op03_with_selected_candidate_shape(
                rdb_status_ref=rdb.P7_R54_AHR_POST_MRB08_RDB_STATUS_BLOCKED_BODYFREE_LEAK_PROMOTION_OR_AUTORUN_REF,
                candidate_ref=rdb.P7_R54_AHR_POST_MRB08_RDB_NEXT_STEP_BLOCKED_POST_MRB08_REF,
                candidate_kind_ref=rdb.P7_R54_AHR_POST_MRB08_RDB_CANDIDATE_KIND_BLOCKED_REF,
                decision_lane_ref=rdb.P7_R54_AHR_POST_MRB08_RDB_DECISION_LANE_BLOCKED_REF,
            ),
        ),
    ],
)
def test_nci_op05_guard_passes_all_valid_next_design_or_stop_material_without_auto_execution(op04: dict[str, object]) -> None:
    material = nci.build_p7_r54_ahr_post_rdb08_nci_op05_bodyfree_no_touch_no_promotion_no_auto_execution_guard(op04)

    assert set(material) == set(nci.P7_R54_AHR_POST_RDB08_NCI_OP05_REQUIRED_FIELD_REFS)
    assert material["schema_version"] == nci.P7_R54_AHR_POST_RDB08_NCI_OP05_SCHEMA_VERSION
    assert material["operation_step_ref"] == nci.P7_R54_AHR_POST_RDB08_NCI_OP05_STEP_REF
    assert material["op04_contract_valid"] is True
    assert material["op04_contract_guard_passed"] is True
    assert material["selected_nci_lane_ref"] == op04["nci_lane_ref"]
    assert material["selected_next_design_target_or_stop_ref"] == op04["next_design_target_or_stop_ref"]
    assert material["selected_next_design_target_or_stop_not_executed"] is True
    assert material["nci_op05_guard_status_ref"] == nci.P7_R54_AHR_POST_RDB08_NCI_OP05_STATUS_GUARD_PASSED_REF
    assert material["bodyfree_guard_passed"] is True
    assert material["no_touch_guard_passed"] is True
    assert material["no_promotion_guard_passed"] is True
    assert material["no_auto_execution_guard_passed"] is True
    assert material["selected_candidate_not_executed_guard_passed"] is True
    assert material["api_db_rn_runtime_response_key_or_p8_question_touch_detected"] is False
    assert material["guard_blocker_refs"] == []
    assert material["forbidden_payload_key_path_refs"] == []
    assert material["body_like_value_path_refs"] == []
    assert material["promotion_claim_refs"] == []
    assert material["no_touch_mutation_path_refs"] == []
    assert material["next_required_step"] == nci.P7_R54_AHR_POST_RDB08_NCI_OP06_STEP_REF
    for key in TRUE_BOUNDARY_KEYS_OP05:
        assert material[key] is True, key
    _assert_no_downstream_execution(material)
    assert nci.assert_p7_r54_ahr_post_rdb08_nci_op05_bodyfree_no_touch_no_promotion_no_auto_execution_guard_contract(material) is True
    _assert_common_bodyfree_no_touch_no_promotion(material)


@pytest.mark.parametrize(
    ("mutation", "evidence_field", "expected_blocker"),
    [
        ({"question_text": "must be blocked"}, "forbidden_payload_key_path_refs", "op04_input_forbidden_payload_key_detected"),
        ({"stdout_body": "must be blocked"}, "body_like_value_path_refs", "op04_input_body_like_value_detected"),
        ({"dhr_op05_called_here": True}, "promotion_claim_refs", "op04_input_promotion_or_autorun_claim_detected"),
        ({"modified_file_refs": ["api/routes/emlis.py"]}, "no_touch_mutation_path_refs", "op04_input_api_db_rn_runtime_response_key_or_p8_question_touch_detected"),
        ({"nci_no_touch_contract": {"api_route_changed": True}}, "no_touch_mutation_path_refs", "op04_input_api_db_rn_runtime_response_key_or_p8_question_touch_detected"),
    ],
)
def test_nci_op05_blocks_bodyfree_no_touch_promotion_or_auto_execution_claims(
    mutation: dict[str, object],
    evidence_field: str,
    expected_blocker: str,
) -> None:
    op04 = _op04_from_op05(_op05_confirmed())
    op04.update(mutation)

    material = nci.build_p7_r54_ahr_post_rdb08_nci_op05_bodyfree_no_touch_no_promotion_no_auto_execution_guard(op04)

    assert material["nci_op05_guard_status_ref"] == nci.P7_R54_AHR_POST_RDB08_NCI_OP05_STATUS_BLOCKED_BODYFREE_PROMOTION_AUTORUN_REF
    assert material["bodyfree_guard_passed"] is False or material["no_touch_guard_passed"] is False or material["no_promotion_guard_passed"] is False
    assert material["selected_next_design_target_or_stop_not_executed"] is False
    assert material[evidence_field]
    assert expected_blocker in material["guard_blocker_refs"]
    assert material["next_required_step"] == nci.P7_R54_AHR_POST_RDB08_NCI_NEXT_STEP_BLOCKED_OP05_GUARD_REF
    _assert_no_downstream_execution(material)
    assert nci.assert_p7_r54_ahr_post_rdb08_nci_op05_bodyfree_no_touch_no_promotion_no_auto_execution_guard_contract(material) is True
    _assert_common_bodyfree_no_touch_no_promotion(material)


def test_nci_op05_repairs_invalid_op04_contract_without_starting_repair_execution() -> None:
    op04 = _op04_from_op05(_op05_confirmed())
    op04["next_required_step"] = nci.P7_R54_AHR_POST_RDB08_NCI_NEXT_DESIGN_DHR_OP05_BOUNDARY_REF

    material = nci.build_p7_r54_ahr_post_rdb08_nci_op05_bodyfree_no_touch_no_promotion_no_auto_execution_guard(op04)

    assert material["nci_op05_guard_status_ref"] == nci.P7_R54_AHR_POST_RDB08_NCI_OP05_STATUS_REPAIR_REQUIRED_REF
    assert material["op04_contract_valid"] is False
    assert material["op04_contract_guard_passed"] is False
    assert material["selected_next_design_target_or_stop_not_executed"] is False
    assert material["guard_blocker_refs"] == ["nci_op04_contract_invalid"]
    assert material["repair_executed_here"] is False
    assert material["next_required_step"] == nci.P7_R54_AHR_POST_RDB08_NCI_NEXT_STEP_REPAIR_OP05_GUARD_REF
    assert nci.assert_p7_r54_ahr_post_rdb08_nci_op05_bodyfree_no_touch_no_promotion_no_auto_execution_guard_contract(material) is True
    _assert_common_bodyfree_no_touch_no_promotion(material)


@pytest.mark.parametrize(
    ("builder", "assertor", "material", "field", "bad_value"),
    [
        (
            nci.build_p7_r54_ahr_post_rdb08_nci_op04_next_design_target_or_stop_materialization,
            nci.assert_p7_r54_ahr_post_rdb08_nci_op04_next_design_target_or_stop_materialization_contract,
            _op03_from_op05(_op05_confirmed()),
            "dhr_op05_builder_called_here",
            True,
        ),
        (
            nci.build_p7_r54_ahr_post_rdb08_nci_op04_next_design_target_or_stop_materialization,
            nci.assert_p7_r54_ahr_post_rdb08_nci_op04_next_design_target_or_stop_materialization_contract,
            _op03_from_op05(_op05_confirmed()),
            "p8_question_substitution_allowed",
            True,
        ),
        (
            nci.build_p7_r54_ahr_post_rdb08_nci_op05_bodyfree_no_touch_no_promotion_no_auto_execution_guard,
            nci.assert_p7_r54_ahr_post_rdb08_nci_op05_bodyfree_no_touch_no_promotion_no_auto_execution_guard_contract,
            _op04_from_op05(_op05_confirmed()),
            "actual_local_human_review_operation_started_here",
            True,
        ),
        (
            nci.build_p7_r54_ahr_post_rdb08_nci_op05_bodyfree_no_touch_no_promotion_no_auto_execution_guard,
            nci.assert_p7_r54_ahr_post_rdb08_nci_op05_bodyfree_no_touch_no_promotion_no_auto_execution_guard_contract,
            _op04_from_op05(_op05_confirmed()),
            "question_text_materialized",
            True,
        ),
    ],
)
def test_nci_op04_op05_contracts_reject_execution_p8_or_guard_mutations(
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


def test_nci_op04_op05_full_title_aliases_match_short_builders_and_asserts() -> None:
    op03 = _op03_from_op05(_op05_confirmed())
    op04_short = nci.build_p7_r54_ahr_post_rdb08_nci_op04_next_design_target_or_stop_materialization(op03)
    op04_alias = nci.build_p7_r54_ahr_post_rdb08_selected_next_stage_candidate_intake_nci_op04_next_design_target_or_stop_materialization(op03)
    assert op04_alias == op04_short
    assert nci.assert_p7_r54_ahr_post_rdb08_selected_next_stage_candidate_intake_nci_op04_next_design_target_or_stop_materialization_contract(op04_alias) is True

    op05_short = nci.build_p7_r54_ahr_post_rdb08_nci_op05_bodyfree_no_touch_no_promotion_no_auto_execution_guard(op04_short)
    op05_alias = nci.build_p7_r54_ahr_post_rdb08_selected_next_stage_candidate_intake_nci_op05_bodyfree_no_touch_no_promotion_no_auto_execution_guard(op04_short)
    assert op05_alias == op05_short
    assert nci.assert_p7_r54_ahr_post_rdb08_selected_next_stage_candidate_intake_nci_op05_bodyfree_no_touch_no_promotion_no_auto_execution_guard_contract(op05_alias) is True
