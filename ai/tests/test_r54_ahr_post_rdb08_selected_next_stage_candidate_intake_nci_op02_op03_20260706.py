# -*- coding: utf-8 -*-
"""R54-AHR Post-RDB08 selected next-stage candidate intake NCI-OP02/OP03 tests."""

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
            "manual_decision_material_ref": f"nci_op02_op03_fixture_{decision_lane_ref}",
            "manual_decision_material_kind_ref": decision_lane_ref,
            "manual_decision_material_present": True,
        }
    )
    return op01


@pytest.mark.parametrize(
    ("op05", "expected_candidate_ref", "expected_candidate_kind", "expected_status"),
    [
        (
            _op05_confirmed(),
            rdb.P7_R54_AHR_POST_MRB08_RDB_NEXT_STEP_PREPARE_DHR_OP05_MANUAL_HANDOFF_DECISION_REF,
            rdb.P7_R54_AHR_POST_MRB08_RDB_CANDIDATE_KIND_DHR_OP05_HANDOFF_REF,
            rdb.P7_R54_AHR_POST_MRB08_RDB_STATUS_CONFIRMED_DHR_OP05_MANUAL_HANDOFF_CANDIDATE_STOPPED_REF,
        ),
        (
            _op05_not_confirmed(),
            rdb.P7_R54_AHR_POST_MRB08_RDB_NEXT_STEP_PREPARE_RETRY_OR_START_DECISION_REF,
            rdb.P7_R54_AHR_POST_MRB08_RDB_CANDIDATE_KIND_RETRY_OR_START_REF,
            rdb.P7_R54_AHR_POST_MRB08_RDB_STATUS_NOT_CONFIRMED_RETRY_OR_START_DECISION_REQUIRED_STOPPED_REF,
        ),
        (
            _op05_waiting_result(),
            rdb.P7_R54_AHR_POST_MRB08_RDB_NEXT_STEP_WAIT_EXTERNAL_BODYFREE_CLAIM_REF,
            rdb.P7_R54_AHR_POST_MRB08_RDB_CANDIDATE_KIND_WAIT_EXTERNAL_CLAIM_REF,
            rdb.P7_R54_AHR_POST_MRB08_RDB_STATUS_WAITING_EXTERNAL_CLAIM_REQUIRED_STOPPED_REF,
        ),
        (
            _op05_invalid_result(),
            rdb.P7_R54_AHR_POST_MRB08_RDB_NEXT_STEP_REPAIR_RESULT_OR_MRB08_REF,
            rdb.P7_R54_AHR_POST_MRB08_RDB_CANDIDATE_KIND_REPAIR_REF,
            rdb.P7_R54_AHR_POST_MRB08_RDB_STATUS_REPAIR_REQUIRED_AFTER_DHR_OP04_RESULT_STOPPED_REF,
        ),
    ],
)
def test_nci_op02_validates_allowed_candidate_shapes_without_execution_or_lane_resolution(
    op05: dict[str, object],
    expected_candidate_ref: str,
    expected_candidate_kind: str,
    expected_status: str,
) -> None:
    material = _op02_from_op05(op05)

    assert set(material) == set(nci.P7_R54_AHR_POST_RDB08_NCI_OP02_REQUIRED_FIELD_REFS)
    assert material["schema_version"] == nci.P7_R54_AHR_POST_RDB08_NCI_OP02_SCHEMA_VERSION
    assert material["operation_step_ref"] == nci.P7_R54_AHR_POST_RDB08_NCI_OP02_STEP_REF
    assert material["op01_contract_valid"] is True
    assert material["op01_ready_for_candidate_shape_validation"] is True
    assert material["rdb08_candidate_ref"] == expected_candidate_ref
    assert material["rdb08_candidate_kind_ref"] == expected_candidate_kind
    assert material["rdb08_selected_status_ref"] == expected_status
    assert material["rdb08_next_required_step_ref"] == expected_candidate_ref
    assert material["candidate_shape_valid"] is True
    assert material["candidate_kind_allowed"] is True
    assert material["candidate_ref_allowed"] is True
    assert material["candidate_ref_matches_kind"] is True
    assert material["candidate_status_allowed"] is True
    assert material["candidate_status_matches_kind_ref_lane"] is True
    assert material["candidate_not_executed_confirmed"] is True
    assert material["candidate_next_required_step_matches_ref"] is True
    assert material["p8_question_candidate_detected"] is False
    assert material["nci_op02_status_ref"] == nci.P7_R54_AHR_POST_RDB08_NCI_OP02_STATUS_READY_FOR_OP03_REF
    assert material["nci_op02_ready_for_lane_resolution"] is True
    assert material["candidate_shape_blocker_refs"] == []
    assert material["next_required_step"] == nci.P7_R54_AHR_POST_RDB08_NCI_OP03_STEP_REF
    assert material["nci_op02_does_not_resolve_selected_candidate_lane"] is True
    assert material["nci_op02_does_not_materialize_next_design_target_or_stop"] is True
    assert material["nci_op02_does_not_execute_selected_next_stage_candidate"] is True
    assert material["nci_op02_does_not_call_dhr_op05"] is True
    assert material["nci_op02_does_not_start_p8_question_design"] is True
    assert nci.assert_p7_r54_ahr_post_rdb08_nci_op02_selected_next_stage_candidate_shape_validation_contract(material) is True
    _assert_common_bodyfree_no_touch_no_promotion(material)


@pytest.mark.parametrize(
    ("mutation", "expected_blocker"),
    [
        ({"selected_next_stage_candidate_ref": "unknown_candidate_ref"}, "candidate_ref_allowed_failed"),
        ({"selected_next_stage_candidate_kind_ref": "unknown_candidate_kind"}, "candidate_kind_allowed_failed"),
        ({"selected_next_stage_candidate_kind_ref": rdb.P7_R54_AHR_POST_MRB08_RDB_CANDIDATE_KIND_RETRY_OR_START_REF}, "candidate_ref_matches_kind_failed"),
        ({"rdb_op08_next_required_step_ref": "mismatched_next_required_step"}, "candidate_next_required_step_matches_ref_failed"),
        ({"selected_next_stage_candidate_not_executed": False}, "candidate_not_executed_confirmed_failed"),
    ],
)
def test_nci_op02_repairs_missing_unknown_or_mismatched_candidate_shape(mutation: dict[str, object], expected_blocker: str) -> None:
    op01 = _op01_from_op05(_op05_confirmed())
    op01.update(mutation)

    material = nci.build_p7_r54_ahr_post_rdb08_nci_op02_selected_next_stage_candidate_shape_validation(op01)

    assert material["nci_op02_status_ref"] == nci.P7_R54_AHR_POST_RDB08_NCI_OP02_STATUS_REPAIR_SELECTED_CANDIDATE_SHAPE_REF
    assert material["candidate_shape_valid"] is False
    assert material["nci_op02_repair_required_for_selected_candidate_shape"] is True
    assert material["next_required_step"] == nci.P7_R54_AHR_POST_RDB08_NCI_NEXT_STEP_REPAIR_CANDIDATE_SHAPE_REF
    assert expected_blocker in material["candidate_shape_blocker_refs"]
    assert material["dhr_op05_called_here"] is False
    assert material["p8_question_design_started"] is False
    assert nci.assert_p7_r54_ahr_post_rdb08_nci_op02_selected_next_stage_candidate_shape_validation_contract(material) is True
    _assert_common_bodyfree_no_touch_no_promotion(material)


@pytest.mark.parametrize(
    ("mutation", "expected_evidence_field"),
    [
        ({"question_text": "must be blocked"}, "op02_input_forbidden_payload_key_path_refs"),
        ({"stdout_body": "must be blocked"}, "op02_input_body_like_value_path_refs"),
        ({"dhr_op05_called_here": True}, "op02_input_promotion_claim_refs"),
        ({"p8_question_substitution_allowed": True}, "op02_input_promotion_claim_refs"),
    ],
)
def test_nci_op02_blocks_bodyfree_leak_promotion_or_p8_question_materialization(
    mutation: dict[str, object],
    expected_evidence_field: str,
) -> None:
    op01 = _op01_from_op05(_op05_confirmed())
    op01.update(mutation)

    material = nci.build_p7_r54_ahr_post_rdb08_nci_op02_selected_next_stage_candidate_shape_validation(op01)

    assert material["nci_op02_status_ref"] == nci.P7_R54_AHR_POST_RDB08_NCI_OP02_STATUS_BLOCKED_BODYFREE_PROMOTION_OR_P8_REF
    assert material["candidate_shape_valid"] is False
    assert material["nci_op02_bodyfree_leak_promotion_or_p8_blocked"] is True
    assert material["next_required_step"] == nci.P7_R54_AHR_POST_RDB08_NCI_NEXT_STEP_BLOCKED_CANDIDATE_SHAPE_REF
    assert material[expected_evidence_field]
    assert material["dhr_op05_called_here"] is False
    assert material["p8_question_design_started"] is False
    assert nci.assert_p7_r54_ahr_post_rdb08_nci_op02_selected_next_stage_candidate_shape_validation_contract(material) is True
    _assert_common_bodyfree_no_touch_no_promotion(material)


@pytest.mark.parametrize(
    ("op05", "expected_status", "expected_lane", "expected_next_ref", "expected_presence_key"),
    [
        (
            _op05_confirmed(),
            nci.P7_R54_AHR_POST_RDB08_NCI_STATUS_DHR_OP05_DESIGN_TARGET_CANDIDATE_STOPPED_REF,
            nci.P7_R54_AHR_POST_RDB08_NCI_LANE_DHR_OP05_DESIGN_TARGET_REF,
            nci.P7_R54_AHR_POST_RDB08_NCI_NEXT_DESIGN_DHR_OP05_BOUNDARY_REF,
            "dhr_op05_design_target_candidate_present",
        ),
        (
            _op05_not_confirmed(),
            nci.P7_R54_AHR_POST_RDB08_NCI_STATUS_RETRY_OR_START_ROUTE_CANDIDATE_STOPPED_REF,
            nci.P7_R54_AHR_POST_RDB08_NCI_LANE_RETRY_OR_START_ROUTE_REF,
            nci.P7_R54_AHR_POST_RDB08_NCI_NEXT_DESIGN_RETRY_OR_START_REF,
            "retry_or_start_route_candidate_present",
        ),
        (
            _op05_waiting_result(),
            nci.P7_R54_AHR_POST_RDB08_NCI_STATUS_WAIT_EXTERNAL_CLAIM_CANDIDATE_STOPPED_REF,
            nci.P7_R54_AHR_POST_RDB08_NCI_LANE_WAIT_EXTERNAL_BODYFREE_CLAIM_REF,
            nci.P7_R54_AHR_POST_RDB08_NCI_NEXT_DESIGN_WAIT_EXTERNAL_CLAIM_REF,
            "external_claim_wait_candidate_present",
        ),
        (
            _op05_invalid_result(),
            nci.P7_R54_AHR_POST_RDB08_NCI_STATUS_REPAIR_ROUTE_CANDIDATE_STOPPED_REF,
            nci.P7_R54_AHR_POST_RDB08_NCI_LANE_REPAIR_RDB_OR_UPSTREAM_RESULT_REF,
            nci.P7_R54_AHR_POST_RDB08_NCI_NEXT_DESIGN_REPAIR_BOUNDARY_REF,
            "repair_route_candidate_present",
        ),
    ],
)
def test_nci_op03_resolves_selected_candidate_lanes_without_downstream_execution(
    op05: dict[str, object],
    expected_status: str,
    expected_lane: str,
    expected_next_ref: str,
    expected_presence_key: str,
) -> None:
    op02 = _op02_from_op05(op05)
    material = nci.build_p7_r54_ahr_post_rdb08_nci_op03_selected_candidate_lane_consistency_resolver(op02)

    assert set(material) == set(nci.P7_R54_AHR_POST_RDB08_NCI_OP03_REQUIRED_FIELD_REFS)
    assert material["schema_version"] == nci.P7_R54_AHR_POST_RDB08_NCI_OP03_SCHEMA_VERSION
    assert material["operation_step_ref"] == nci.P7_R54_AHR_POST_RDB08_NCI_OP03_STEP_REF
    assert material["op02_contract_valid"] is True
    assert material["op02_candidate_shape_valid"] is True
    assert material["candidate_lane_consistency_checked"] is True
    assert material["candidate_lane_consistent"] is True
    assert material["candidate_lane_consistency_blocker_refs"] == []
    assert material["nci_status_ref"] == expected_status
    assert material["nci_lane_ref"] == expected_lane
    assert material["selected_next_design_or_stop_ref"] == expected_next_ref
    assert material["selected_next_design_or_stop_not_executed"] is True
    assert material["selected_next_stage_candidate_not_executed_preserved"] is True
    assert material["exactly_one_nci_lane_selected"] is True
    assert material[expected_presence_key] is True
    assert sum(
        1
        for key in (
            "dhr_op05_design_target_candidate_present",
            "retry_or_start_route_candidate_present",
            "external_claim_wait_candidate_present",
            "repair_route_candidate_present",
            "unresolved_manual_hold_candidate_present",
            "blocked_candidate_present",
        )
        if material[key] is True
    ) == 1
    assert material["dhr_op05_call_allowed_here"] is False
    assert material["dhr_op05_builder_called_here"] is False
    assert material["dhr_op06_builder_called_here"] is False
    assert material["dmd_builder_called_here"] is False
    assert material["r52_actual_execution_called_here"] is False
    assert material["actual_local_human_review_operation_started_here"] is False
    assert material["raw_evidence_request_created_here"] is False
    assert material["repair_executed_here"] is False
    assert material["p8_question_substitution_allowed"] is False
    assert material["question_text_materialized"] is False
    assert material["next_required_step"] == nci.P7_R54_AHR_POST_RDB08_NCI_OP04_STEP_REF
    assert nci.assert_p7_r54_ahr_post_rdb08_nci_op03_selected_candidate_lane_consistency_resolver_contract(material) is True
    _assert_common_bodyfree_no_touch_no_promotion(material)


@pytest.mark.parametrize(
    (
        "rdb_status_ref",
        "candidate_ref",
        "candidate_kind_ref",
        "decision_lane_ref",
        "expected_nci_status_ref",
        "expected_nci_lane_ref",
        "expected_next_ref",
        "expected_presence_key",
        "expected_lane_consistent",
        "expected_next_required_step",
    ),
    [
        (
            rdb.P7_R54_AHR_POST_MRB08_RDB_STATUS_INCOMPLETE_UNRESOLVED_MANUAL_HOLD_STOPPED_REF,
            rdb.P7_R54_AHR_POST_MRB08_RDB_NEXT_STEP_MANUAL_HOLD_UNRESOLVED_REF,
            rdb.P7_R54_AHR_POST_MRB08_RDB_CANDIDATE_KIND_UNRESOLVED_REF,
            rdb.P7_R54_AHR_POST_MRB08_RDB_DECISION_LANE_MANUAL_HOLD_UNRESOLVED_REF,
            nci.P7_R54_AHR_POST_RDB08_NCI_STATUS_MANUAL_HOLD_UNRESOLVED_STOPPED_REF,
            nci.P7_R54_AHR_POST_RDB08_NCI_LANE_MANUAL_HOLD_UNRESOLVED_REF,
            nci.P7_R54_AHR_POST_RDB08_NCI_NEXT_STOP_MANUAL_HOLD_REF,
            "unresolved_manual_hold_candidate_present",
            True,
            nci.P7_R54_AHR_POST_RDB08_NCI_OP04_STEP_REF,
        ),
        (
            rdb.P7_R54_AHR_POST_MRB08_RDB_STATUS_BLOCKED_BODYFREE_LEAK_PROMOTION_OR_AUTORUN_REF,
            rdb.P7_R54_AHR_POST_MRB08_RDB_NEXT_STEP_BLOCKED_POST_MRB08_REF,
            rdb.P7_R54_AHR_POST_MRB08_RDB_CANDIDATE_KIND_BLOCKED_REF,
            rdb.P7_R54_AHR_POST_MRB08_RDB_DECISION_LANE_BLOCKED_REF,
            nci.P7_R54_AHR_POST_RDB08_NCI_STATUS_BLOCKED_SELECTED_CANDIDATE_STOPPED_REF,
            nci.P7_R54_AHR_POST_RDB08_NCI_LANE_BLOCKED_BODYFREE_PROMOTION_AUTORUN_REF,
            nci.P7_R54_AHR_POST_RDB08_NCI_NEXT_STOP_BLOCKED_REF,
            "blocked_candidate_present",
            False,
            nci.P7_R54_AHR_POST_RDB08_NCI_NEXT_STOP_BLOCKED_REF,
        ),
    ],
)
def test_nci_op02_op03_cover_unresolved_and_blocked_selected_candidate_lanes_without_execution(
    rdb_status_ref: str,
    candidate_ref: str,
    candidate_kind_ref: str,
    decision_lane_ref: str,
    expected_nci_status_ref: str,
    expected_nci_lane_ref: str,
    expected_next_ref: str,
    expected_presence_key: str,
    expected_lane_consistent: bool,
    expected_next_required_step: str,
) -> None:
    op01 = _op01_with_selected_candidate_shape(
        rdb_status_ref=rdb_status_ref,
        candidate_ref=candidate_ref,
        candidate_kind_ref=candidate_kind_ref,
        decision_lane_ref=decision_lane_ref,
    )
    op02 = nci.build_p7_r54_ahr_post_rdb08_nci_op02_selected_next_stage_candidate_shape_validation(op01)

    assert op02["candidate_shape_valid"] is True
    assert op02["candidate_shape_blocker_refs"] == []
    assert op02["nci_op02_ready_for_lane_resolution"] is True
    assert op02["rdb08_candidate_ref"] == candidate_ref
    assert op02["rdb08_candidate_kind_ref"] == candidate_kind_ref
    assert nci.assert_p7_r54_ahr_post_rdb08_nci_op02_selected_next_stage_candidate_shape_validation_contract(op02) is True

    material = nci.build_p7_r54_ahr_post_rdb08_nci_op03_selected_candidate_lane_consistency_resolver(op02)

    assert material["nci_status_ref"] == expected_nci_status_ref
    assert material["nci_lane_ref"] == expected_nci_lane_ref
    assert material["selected_next_design_or_stop_ref"] == expected_next_ref
    assert material[expected_presence_key] is True
    assert material["exactly_one_nci_lane_selected"] is True
    assert material["candidate_lane_consistent"] is expected_lane_consistent
    assert material["next_required_step"] == expected_next_required_step
    assert material["selected_next_design_or_stop_not_executed"] is True
    assert material["dhr_op05_builder_called_here"] is False
    assert material["actual_local_human_review_operation_started_here"] is False
    assert material["repair_executed_here"] is False
    assert material["p8_question_substitution_allowed"] is False
    assert nci.assert_p7_r54_ahr_post_rdb08_nci_op03_selected_candidate_lane_consistency_resolver_contract(material) is True
    _assert_common_bodyfree_no_touch_no_promotion(material)


def test_nci_op03_resolves_op02_repair_shape_to_repair_lane_without_repair_execution() -> None:
    op01 = _op01_from_op05(_op05_confirmed())
    op01["selected_next_stage_candidate_kind_ref"] = "unknown_candidate_kind"
    op02 = nci.build_p7_r54_ahr_post_rdb08_nci_op02_selected_next_stage_candidate_shape_validation(op01)

    material = nci.build_p7_r54_ahr_post_rdb08_nci_op03_selected_candidate_lane_consistency_resolver(op02)

    assert material["nci_status_ref"] == nci.P7_R54_AHR_POST_RDB08_NCI_STATUS_REPAIR_ROUTE_CANDIDATE_STOPPED_REF
    assert material["nci_lane_ref"] == nci.P7_R54_AHR_POST_RDB08_NCI_LANE_REPAIR_RDB_OR_UPSTREAM_RESULT_REF
    assert material["repair_route_candidate_present"] is True
    assert material["candidate_lane_consistent"] is False
    assert material["candidate_lane_consistency_blocker_refs"]
    assert material["repair_executed_here"] is False
    assert material["next_required_step"] == nci.P7_R54_AHR_POST_RDB08_NCI_NEXT_STEP_REPAIR_LANE_CONSISTENCY_REF
    assert nci.assert_p7_r54_ahr_post_rdb08_nci_op03_selected_candidate_lane_consistency_resolver_contract(material) is True
    _assert_common_bodyfree_no_touch_no_promotion(material)


def test_nci_op03_resolves_op02_blocked_shape_to_blocked_lane_without_continuing_to_op04() -> None:
    op01 = _op01_from_op05(_op05_confirmed())
    op01["question_text"] = "must be blocked"
    op02 = nci.build_p7_r54_ahr_post_rdb08_nci_op02_selected_next_stage_candidate_shape_validation(op01)

    material = nci.build_p7_r54_ahr_post_rdb08_nci_op03_selected_candidate_lane_consistency_resolver(op02)

    assert material["nci_status_ref"] == nci.P7_R54_AHR_POST_RDB08_NCI_STATUS_BLOCKED_SELECTED_CANDIDATE_STOPPED_REF
    assert material["nci_lane_ref"] == nci.P7_R54_AHR_POST_RDB08_NCI_LANE_BLOCKED_BODYFREE_PROMOTION_AUTORUN_REF
    assert material["blocked_candidate_present"] is True
    assert material["candidate_lane_consistent"] is False
    assert material["candidate_lane_consistency_blocker_refs"]
    assert material["selected_next_design_or_stop_ref"] == nci.P7_R54_AHR_POST_RDB08_NCI_NEXT_STOP_BLOCKED_REF
    assert material["next_required_step"] == nci.P7_R54_AHR_POST_RDB08_NCI_NEXT_STOP_BLOCKED_REF
    assert material["dhr_op05_builder_called_here"] is False
    assert material["p8_question_substitution_allowed"] is False
    assert nci.assert_p7_r54_ahr_post_rdb08_nci_op03_selected_candidate_lane_consistency_resolver_contract(material) is True
    _assert_common_bodyfree_no_touch_no_promotion(material)


@pytest.mark.parametrize(
    ("field", "bad_value"),
    [
        ("dhr_op05_builder_called_here", True),
        ("actual_local_human_review_operation_started_here", True),
        ("raw_evidence_request_created_here", True),
        ("repair_executed_here", True),
        ("p8_question_substitution_allowed", True),
        ("question_text_materialized", True),
        ("next_required_step", nci.P7_R54_AHR_POST_RDB08_NCI_NEXT_DESIGN_DHR_OP05_BOUNDARY_REF),
    ],
)
def test_nci_op03_contract_rejects_downstream_execution_p8_or_next_step_mutations(field: str, bad_value: object) -> None:
    material = nci.build_p7_r54_ahr_post_rdb08_nci_op03_selected_candidate_lane_consistency_resolver(
        _op02_from_op05(_op05_confirmed()),
    )
    material[field] = bad_value

    with pytest.raises(ValueError):
        nci.assert_p7_r54_ahr_post_rdb08_nci_op03_selected_candidate_lane_consistency_resolver_contract(material)


def test_nci_op02_op03_full_title_aliases_match_short_builders_and_asserts() -> None:
    op01 = _op01_from_op05(_op05_confirmed())
    op02_short = nci.build_p7_r54_ahr_post_rdb08_nci_op02_selected_next_stage_candidate_shape_validation(op01)
    op02_alias = nci.build_p7_r54_ahr_post_rdb08_selected_next_stage_candidate_intake_nci_op02_selected_next_stage_candidate_shape_validation(op01)
    assert op02_alias == op02_short
    assert nci.assert_p7_r54_ahr_post_rdb08_selected_next_stage_candidate_intake_nci_op02_selected_next_stage_candidate_shape_validation_contract(op02_alias) is True

    op03_short = nci.build_p7_r54_ahr_post_rdb08_nci_op03_selected_candidate_lane_consistency_resolver(op02_short)
    op03_alias = nci.build_p7_r54_ahr_post_rdb08_selected_next_stage_candidate_intake_nci_op03_selected_candidate_lane_consistency_resolver(op02_short)
    assert op03_alias == op03_short
    assert nci.assert_p7_r54_ahr_post_rdb08_selected_next_stage_candidate_intake_nci_op03_selected_candidate_lane_consistency_resolver_contract(op03_alias) is True
