# -*- coding: utf-8 -*-
"""R54-AHR Post-RDB08 selected next-stage candidate intake NCI-OP00/OP01 tests."""

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


def _confirmed_rdb_op08() -> dict[str, object]:
    return _op08_from_op05(_op05_confirmed())


def test_nci_op00_refreezes_scope_no_execution_no_promotion_after_rdb_op08() -> None:
    material = nci.build_p7_r54_ahr_post_rdb08_nci_op00_scope_no_execution_no_promotion_refreeze_after_rdb_op08()

    assert set(material) == set(nci.P7_R54_AHR_POST_RDB08_NCI_OP00_REQUIRED_FIELD_REFS)
    assert material["schema_version"] == nci.P7_R54_AHR_POST_RDB08_NCI_OP00_SCHEMA_VERSION
    assert material["operation_step_ref"] == nci.P7_R54_AHR_POST_RDB08_NCI_OP00_STEP_REF
    assert material["selected_stage_ref"] == nci.P7_R54_AHR_POST_RDB08_NCI_SELECTED_STAGE_REF
    assert material["selected_design_target_ref"] == nci.P7_R54_AHR_POST_RDB08_NCI_SELECTED_DESIGN_TARGET_REF
    assert material["boundary_prefix_ref"] == "NCI"
    assert material["boundary_prefix_meaning_ref"] == "Next Candidate Intake"
    assert material["source_mode_local_received_zip_only_confirmed"] is True
    assert material["github_connection_check_not_required_by_mash_instruction"] is True
    assert material["github_connection_check_performed"] is False
    assert material["nci_op00_scope_confirmed"] is True
    assert material["nci_op00_no_execution_boundary_confirmed"] is True
    assert material["nci_op00_no_touch_boundary_confirmed"] is True
    assert material["nci_op00_no_promotion_boundary_confirmed"] is True
    assert material["nci_op00_does_not_intake_rdb_op08_result_memo"] is True
    assert material["nci_op00_does_not_execute_selected_next_stage_candidate"] is True
    assert material["nci_op00_does_not_call_dhr_op05"] is True
    assert material["nci_op00_does_not_start_p8_question_design"] is True
    assert material["nci_op00_does_not_change_api_db_rn_runtime_response_key"] is True
    assert material["selected_next_stage_candidate_executed_here"] is False
    assert material["candidate_execution_started_here"] is False
    assert material["implemented_steps"] == list(nci.P7_R54_AHR_POST_RDB08_NCI_OP00_IMPLEMENTED_STEPS)
    assert material["not_yet_implemented_steps"] == list(nci.P7_R54_AHR_POST_RDB08_NCI_OP00_NOT_YET_IMPLEMENTED_STEPS)
    assert material["next_required_step"] == nci.P7_R54_AHR_POST_RDB08_NCI_OP01_STEP_REF
    assert nci.assert_p7_r54_ahr_post_rdb08_nci_op00_scope_no_execution_no_promotion_refreeze_after_rdb_op08_contract(material) is True
    _assert_common_bodyfree_no_touch_no_promotion(material)


@pytest.mark.parametrize(
    ("field", "bad_value"),
    [
        ("schema_version", "bad_schema"),
        ("source_mode", "github_remote"),
        ("git_checked", True),
        ("github_connection_check_performed", True),
        ("nci_op00_no_execution_boundary_confirmed", False),
        ("nci_op00_no_touch_boundary_confirmed", False),
        ("nci_op00_no_promotion_boundary_confirmed", False),
        ("nci_op00_does_not_execute_selected_next_stage_candidate", False),
        ("nci_op00_does_not_call_dhr_op05", False),
        ("body_free", False),
        ("selected_next_stage_candidate_executed_here", True),
        ("candidate_execution_started_here", True),
        ("dhr_op05_called_here", True),
        ("p8_start_allowed", True),
        ("release_allowed", True),
        ("next_required_step", nci.P7_R54_AHR_POST_RDB08_NCI_OP02_STEP_REF),
    ],
)
def test_nci_op00_contract_rejects_scope_execution_promotion_or_next_step_mutations(field: str, bad_value: object) -> None:
    material = nci.build_p7_r54_ahr_post_rdb08_nci_op00_scope_no_execution_no_promotion_refreeze_after_rdb_op08()
    material[field] = bad_value

    with pytest.raises(ValueError):
        nci.assert_p7_r54_ahr_post_rdb08_nci_op00_scope_no_execution_no_promotion_refreeze_after_rdb_op08_contract(material)


def test_nci_op00_contract_rejects_public_contract_marker_mutation() -> None:
    material = nci.build_p7_r54_ahr_post_rdb08_nci_op00_scope_no_execution_no_promotion_refreeze_after_rdb_op08()
    material["public_contract"]["api_response_key_added"] = True

    with pytest.raises(ValueError):
        nci.assert_p7_r54_ahr_post_rdb08_nci_op00_scope_no_execution_no_promotion_refreeze_after_rdb_op08_contract(material)


def test_nci_op00_contract_rejects_forbidden_top_level_body_payload_key() -> None:
    material = nci.build_p7_r54_ahr_post_rdb08_nci_op00_scope_no_execution_no_promotion_refreeze_after_rdb_op08()
    material["comment_text"] = "must never pass"

    with pytest.raises(ValueError):
        nci.assert_p7_r54_ahr_post_rdb08_nci_op00_scope_no_execution_no_promotion_refreeze_after_rdb_op08_contract(material)


def test_nci_op01_accepts_valid_rdb_op08_bodyfree_closure_without_candidate_execution() -> None:
    rdb_op08 = _confirmed_rdb_op08()
    material = nci.build_p7_r54_ahr_post_rdb08_nci_op01_rdb_op08_bodyfree_result_memo_closure_intake(
        rdb_op08_bodyfree_result_memo_closure=rdb_op08,
    )

    assert set(material) == set(nci.P7_R54_AHR_POST_RDB08_NCI_OP01_REQUIRED_FIELD_REFS)
    assert material["schema_version"] == nci.P7_R54_AHR_POST_RDB08_NCI_OP01_SCHEMA_VERSION
    assert material["operation_step_ref"] == nci.P7_R54_AHR_POST_RDB08_NCI_OP01_STEP_REF
    assert material["op00_contract_valid"] is True
    assert material["rdb_op08_material_present"] is True
    assert material["rdb_op08_contract_valid"] is True
    assert material["rdb_op08_status_ref"] == rdb.P7_R54_AHR_POST_MRB08_RDB_OP08_STATUS_CLOSED_BODYFREE_STOPPED_REF
    assert material["bodyfree_result_manual_decision_memo_closure_status_ref"] == material["rdb_op08_status_ref"]
    assert material["rdb_op08_closed_bodyfree_stopped"] is True
    assert material["rdb_selected_status_ref"] == rdb.P7_R54_AHR_POST_MRB08_RDB_STATUS_CONFIRMED_DHR_OP05_MANUAL_HANDOFF_CANDIDATE_STOPPED_REF
    assert material["manual_decision_material_present"] is True
    assert material["selected_next_stage_candidate_ref"] == rdb.P7_R54_AHR_POST_MRB08_RDB_NEXT_STEP_PREPARE_DHR_OP05_MANUAL_HANDOFF_DECISION_REF
    assert material["selected_next_stage_candidate_kind_ref"] == rdb.P7_R54_AHR_POST_MRB08_RDB_CANDIDATE_KIND_DHR_OP05_HANDOFF_REF
    assert material["selected_next_stage_candidate_not_executed"] is True
    assert material["nci_op01_status_ref"] == nci.P7_R54_AHR_POST_RDB08_NCI_OP01_STATUS_READY_FOR_OP02_REF
    assert material["nci_op01_ready_for_candidate_shape_validation"] is True
    assert material["nci_op01_blocker_refs"] == []
    assert material["rdb_op08_input_forbidden_payload_key_path_refs"] == []
    assert material["rdb_op08_input_body_like_value_path_refs"] == []
    assert material["rdb_op08_input_promotion_claim_refs"] == []
    assert material["next_required_step"] == nci.P7_R54_AHR_POST_RDB08_NCI_OP02_STEP_REF
    assert material["rdb_op08_closure_is_not_candidate_execution"] is True
    assert material["nci_op01_does_not_validate_candidate_shape"] is True
    assert material["nci_op01_does_not_resolve_selected_candidate_lane"] is True
    assert material["nci_op01_does_not_materialize_next_design_target_or_stop"] is True
    assert material["nci_op01_does_not_execute_selected_next_stage_candidate"] is True
    assert material["nci_op01_does_not_call_dhr_op05"] is True
    assert material["dhr_op05_called_here"] is False
    assert material["dhr_op06_called_here"] is False
    assert material["dmd_execution_started_here"] is False
    assert material["r52_actual_execution_started_here"] is False
    assert material["p8_start_allowed"] is False
    assert material["p8_question_design_started"] is False
    assert material["release_allowed"] is False
    assert material["rdb_target_green_confirmed"] is True
    assert material["selected_regression_green_confirmed"] is True
    assert material["compileall_green_confirmed"] is True
    assert material["full_backend_suite_green_confirmed"] is False
    assert material["rn_contract_green_confirmed"] is False
    assert material["rn_real_device_modal_verified_claimed_here"] is False
    assert material["implemented_steps"] == list(nci.P7_R54_AHR_POST_RDB08_NCI_OP01_IMPLEMENTED_STEPS)
    assert material["not_yet_implemented_steps"] == list(nci.P7_R54_AHR_POST_RDB08_NCI_OP01_NOT_YET_IMPLEMENTED_STEPS)
    assert nci.assert_p7_r54_ahr_post_rdb08_nci_op01_rdb_op08_bodyfree_result_memo_closure_intake_contract(material) is True
    _assert_common_bodyfree_no_touch_no_promotion(material)


def test_nci_op01_accepts_manual_decision_named_rdb_op08_keyword_alias() -> None:
    material = nci.build_p7_r54_ahr_post_rdb08_nci_op01_rdb_op08_bodyfree_result_memo_closure_intake(
        rdb_op08_bodyfree_result_manual_decision_memo_closure=_confirmed_rdb_op08(),
    )

    assert material["nci_op01_status_ref"] == nci.P7_R54_AHR_POST_RDB08_NCI_OP01_STATUS_READY_FOR_OP02_REF
    assert material["nci_op01_ready_for_candidate_shape_validation"] is True
    assert nci.assert_p7_r54_ahr_post_rdb08_nci_op01_rdb_op08_bodyfree_result_memo_closure_intake_contract(material) is True


@pytest.mark.parametrize(
    ("op05", "expected_status", "expected_candidate_ref", "expected_candidate_kind"),
    [
        (
            _op05_confirmed(),
            rdb.P7_R54_AHR_POST_MRB08_RDB_STATUS_CONFIRMED_DHR_OP05_MANUAL_HANDOFF_CANDIDATE_STOPPED_REF,
            rdb.P7_R54_AHR_POST_MRB08_RDB_NEXT_STEP_PREPARE_DHR_OP05_MANUAL_HANDOFF_DECISION_REF,
            rdb.P7_R54_AHR_POST_MRB08_RDB_CANDIDATE_KIND_DHR_OP05_HANDOFF_REF,
        ),
        (
            _op05_not_confirmed(),
            rdb.P7_R54_AHR_POST_MRB08_RDB_STATUS_NOT_CONFIRMED_RETRY_OR_START_DECISION_REQUIRED_STOPPED_REF,
            rdb.P7_R54_AHR_POST_MRB08_RDB_NEXT_STEP_PREPARE_RETRY_OR_START_DECISION_REF,
            rdb.P7_R54_AHR_POST_MRB08_RDB_CANDIDATE_KIND_RETRY_OR_START_REF,
        ),
        (
            _op05_waiting_result(),
            rdb.P7_R54_AHR_POST_MRB08_RDB_STATUS_WAITING_EXTERNAL_CLAIM_REQUIRED_STOPPED_REF,
            rdb.P7_R54_AHR_POST_MRB08_RDB_NEXT_STEP_WAIT_EXTERNAL_BODYFREE_CLAIM_REF,
            rdb.P7_R54_AHR_POST_MRB08_RDB_CANDIDATE_KIND_WAIT_EXTERNAL_CLAIM_REF,
        ),
        (
            _op05_invalid_result(),
            rdb.P7_R54_AHR_POST_MRB08_RDB_STATUS_REPAIR_REQUIRED_AFTER_DHR_OP04_RESULT_STOPPED_REF,
            rdb.P7_R54_AHR_POST_MRB08_RDB_NEXT_STEP_REPAIR_RESULT_OR_MRB08_REF,
            rdb.P7_R54_AHR_POST_MRB08_RDB_CANDIDATE_KIND_REPAIR_REF,
        ),
    ],
)
def test_nci_op01_intakes_all_valid_rdb_op08_candidate_kinds_but_does_not_resolve_lane_yet(
    op05: dict[str, object],
    expected_status: str,
    expected_candidate_ref: str,
    expected_candidate_kind: str,
) -> None:
    material = nci.build_p7_r54_ahr_post_rdb08_nci_op01_rdb_op08_bodyfree_result_memo_closure_intake(
        rdb_op08_bodyfree_result_memo_closure=_op08_from_op05(op05),
    )

    assert material["nci_op01_status_ref"] == nci.P7_R54_AHR_POST_RDB08_NCI_OP01_STATUS_READY_FOR_OP02_REF
    assert material["nci_op01_ready_for_candidate_shape_validation"] is True
    assert material["rdb_selected_status_ref"] == expected_status
    assert material["selected_next_stage_candidate_ref"] == expected_candidate_ref
    assert material["selected_next_stage_candidate_kind_ref"] == expected_candidate_kind
    assert material["selected_next_stage_candidate_not_executed"] is True
    assert material["nci_op01_does_not_validate_candidate_shape"] is True
    assert material["nci_op01_does_not_resolve_selected_candidate_lane"] is True
    assert material["nci_op01_does_not_materialize_next_design_target_or_stop"] is True
    assert material["nci_op01_does_not_execute_selected_next_stage_candidate"] is True
    assert material["dhr_op05_called_here"] is False
    assert material["p8_question_design_started"] is False
    assert nci.assert_p7_r54_ahr_post_rdb08_nci_op01_rdb_op08_bodyfree_result_memo_closure_intake_contract(material) is True
    _assert_common_bodyfree_no_touch_no_promotion(material)


def test_nci_op01_waits_when_rdb_op08_result_memo_is_missing() -> None:
    material = nci.build_p7_r54_ahr_post_rdb08_nci_op01_rdb_op08_bodyfree_result_memo_closure_intake()

    assert material["nci_op01_status_ref"] == nci.P7_R54_AHR_POST_RDB08_NCI_OP01_STATUS_WAITING_FOR_RDB08_CLOSURE_REF
    assert material["nci_op01_waiting_for_rdb08_closure"] is True
    assert "rdb_op08_result_memo_closure_missing" in material["nci_op01_blocker_refs"]
    assert material["next_required_step"] == nci.P7_R54_AHR_POST_RDB08_NCI_NEXT_STEP_WAIT_FOR_RDB08_CLOSURE_REF
    assert material["dhr_op05_called_here"] is False
    assert nci.assert_p7_r54_ahr_post_rdb08_nci_op01_rdb_op08_bodyfree_result_memo_closure_intake_contract(material) is True
    _assert_common_bodyfree_no_touch_no_promotion(material)


def test_nci_op01_repairs_when_op00_contract_is_invalid() -> None:
    op00 = nci.build_p7_r54_ahr_post_rdb08_nci_op00_scope_no_execution_no_promotion_refreeze_after_rdb_op08()
    op00["next_required_step"] = nci.P7_R54_AHR_POST_RDB08_NCI_OP02_STEP_REF

    material = nci.build_p7_r54_ahr_post_rdb08_nci_op01_rdb_op08_bodyfree_result_memo_closure_intake(
        scope_no_execution_no_promotion_refreeze_after_rdb_op08=op00,
        rdb_op08_bodyfree_result_memo_closure=_confirmed_rdb_op08(),
    )

    assert material["op00_contract_valid"] is False
    assert material["nci_op01_status_ref"] == nci.P7_R54_AHR_POST_RDB08_NCI_OP01_STATUS_REPAIR_RDB08_INTAKE_REF
    assert material["nci_op01_repair_required"] is True
    assert "nci_op00_contract_invalid" in material["nci_op01_blocker_refs"]
    assert material["next_required_step"] == nci.P7_R54_AHR_POST_RDB08_NCI_NEXT_STEP_REPAIR_RDB08_INTAKE_REF
    assert nci.assert_p7_r54_ahr_post_rdb08_nci_op01_rdb_op08_bodyfree_result_memo_closure_intake_contract(material) is True


def test_nci_op01_repairs_when_rdb_op08_contract_is_invalid() -> None:
    rdb_op08 = deepcopy(_confirmed_rdb_op08())
    rdb_op08["selected_next_stage_candidate_not_executed"] = False
    material = nci.build_p7_r54_ahr_post_rdb08_nci_op01_rdb_op08_bodyfree_result_memo_closure_intake(
        rdb_op08_bodyfree_result_memo_closure=rdb_op08,
    )

    assert material["rdb_op08_contract_valid"] is False
    assert material["nci_op01_status_ref"] == nci.P7_R54_AHR_POST_RDB08_NCI_OP01_STATUS_REPAIR_RDB08_INTAKE_REF
    assert material["nci_op01_repair_required"] is True
    assert "rdb_op08_result_memo_closure_contract_invalid" in material["nci_op01_blocker_refs"]
    assert material["selected_next_stage_candidate_not_executed"] is False
    assert material["next_required_step"] == nci.P7_R54_AHR_POST_RDB08_NCI_NEXT_STEP_REPAIR_RDB08_INTAKE_REF
    assert nci.assert_p7_r54_ahr_post_rdb08_nci_op01_rdb_op08_bodyfree_result_memo_closure_intake_contract(material) is True


@pytest.mark.parametrize(
    ("mutation_key", "mutation_value", "expected_blocker", "expected_path_field"),
    [
        (
            "question_text",
            "must be blocked",
            "rdb_op08_input_forbidden_payload_key_detected",
            "rdb_op08_input_forbidden_payload_key_path_refs",
        ),
        (
            "dhr_op05_called_here",
            True,
            "rdb_op08_input_promotion_or_autorun_claim_detected",
            "rdb_op08_input_promotion_claim_refs",
        ),
        (
            "stdout_body",
            "must be blocked",
            "rdb_op08_input_body_like_value_detected",
            "rdb_op08_input_body_like_value_path_refs",
        ),
    ],
)
def test_nci_op01_blocks_rdb_op08_bodyfree_leak_or_promotion_claims(
    mutation_key: str,
    mutation_value: object,
    expected_blocker: str,
    expected_path_field: str,
) -> None:
    rdb_op08 = deepcopy(_confirmed_rdb_op08())
    rdb_op08[mutation_key] = mutation_value

    material = nci.build_p7_r54_ahr_post_rdb08_nci_op01_rdb_op08_bodyfree_result_memo_closure_intake(
        rdb_op08_bodyfree_result_memo_closure=rdb_op08,
    )

    assert material["nci_op01_status_ref"] == nci.P7_R54_AHR_POST_RDB08_NCI_OP01_STATUS_BLOCKED_BODYFREE_PROMOTION_AUTORUN_REF
    assert material["nci_op01_bodyfree_leak_promotion_or_autorun_blocked"] is True
    assert expected_blocker in material["nci_op01_blocker_refs"]
    assert any(str(path).startswith("rdb_op08_bodyfree_result_memo_closure.") for path in material[expected_path_field])
    assert material["next_required_step"] == nci.P7_R54_AHR_POST_RDB08_NCI_NEXT_STEP_BLOCKED_RDB08_INTAKE_REF
    assert nci.assert_p7_r54_ahr_post_rdb08_nci_op01_rdb_op08_bodyfree_result_memo_closure_intake_contract(material) is True


def test_nci_op01_contract_rejects_ready_branch_promotion_mutation() -> None:
    material = nci.build_p7_r54_ahr_post_rdb08_nci_op01_rdb_op08_bodyfree_result_memo_closure_intake(
        rdb_op08_bodyfree_result_memo_closure=_confirmed_rdb_op08(),
    )
    material["dhr_op05_called_here"] = True

    with pytest.raises(ValueError):
        nci.assert_p7_r54_ahr_post_rdb08_nci_op01_rdb_op08_bodyfree_result_memo_closure_intake_contract(material)


def test_nci_op01_contract_rejects_ready_branch_with_blocker() -> None:
    material = nci.build_p7_r54_ahr_post_rdb08_nci_op01_rdb_op08_bodyfree_result_memo_closure_intake(
        rdb_op08_bodyfree_result_memo_closure=_confirmed_rdb_op08(),
    )
    material["nci_op01_blocker_refs"] = ["synthetic_blocker"]
    material["nci_op01_blocker_ref_count"] = 1

    with pytest.raises(ValueError):
        nci.assert_p7_r54_ahr_post_rdb08_nci_op01_rdb_op08_bodyfree_result_memo_closure_intake_contract(material)


def test_nci_op01_contract_rejects_non_ready_branch_that_continues_to_op02() -> None:
    material = nci.build_p7_r54_ahr_post_rdb08_nci_op01_rdb_op08_bodyfree_result_memo_closure_intake()
    material["next_required_step"] = nci.P7_R54_AHR_POST_RDB08_NCI_OP02_STEP_REF

    with pytest.raises(ValueError):
        nci.assert_p7_r54_ahr_post_rdb08_nci_op01_rdb_op08_bodyfree_result_memo_closure_intake_contract(material)


def test_nci_op00_op01_full_title_aliases_match_short_builders_and_asserts() -> None:
    op00 = nci.build_p7_r54_ahr_post_rdb08_selected_next_stage_candidate_intake_nci_op00_scope_no_execution_no_promotion_refreeze_after_rdb_op08()
    op01 = nci.build_p7_r54_ahr_post_rdb08_selected_next_stage_candidate_intake_nci_op01_rdb_op08_bodyfree_result_memo_closure_intake(
        rdb_op08_bodyfree_result_memo_closure=_confirmed_rdb_op08(),
    )

    assert op00 == nci.build_p7_r54_ahr_post_rdb08_nci_op00_scope_no_execution_no_promotion_refreeze_after_rdb_op08()
    assert op01 == nci.build_p7_r54_ahr_post_rdb08_nci_op01_rdb_op08_bodyfree_result_memo_closure_intake(
        rdb_op08_bodyfree_result_memo_closure=_confirmed_rdb_op08(),
    )
    assert nci.assert_p7_r54_ahr_post_rdb08_selected_next_stage_candidate_intake_nci_op00_scope_no_execution_no_promotion_refreeze_after_rdb_op08_contract(op00) is True
    assert nci.assert_p7_r54_ahr_post_rdb08_selected_next_stage_candidate_intake_nci_op01_rdb_op08_bodyfree_result_memo_closure_intake_contract(op01) is True
