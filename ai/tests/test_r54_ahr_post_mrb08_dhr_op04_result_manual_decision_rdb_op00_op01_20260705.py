# -*- coding: utf-8 -*-
"""R54-AHR Post-MRB08 / DHR-OP04 result manual decision RDB-OP00/OP01 tests."""

from __future__ import annotations

from pathlib import Path
import sys

import pytest

TEST_DIR = Path(__file__).resolve().parent
if str(TEST_DIR) not in sys.path:
    sys.path.insert(0, str(TEST_DIR))

import emlis_ai_p7_r54_ahr_post_mrb08_dhr_op04_result_manual_decision_20260705 as rdb
import emlis_ai_p7_r54_ahr_post_dri_dhr_op04_manual_reintake_20260705 as mrb
import emlis_ai_p7_r54_ahr_post_elr19_downstream_manual_decision_handoff_or_retry_20260704 as dhr
from test_r54_ahr_post_dri_dhr_op04_manual_reintake_mrb_op06_op07_20260705 import (
    _op05_confirmed,
    _op05_invalid_result,
    _op05_not_confirmed,
    _op05_waiting_result,
)
from test_r54_ahr_post_dri_dhr_op04_manual_reintake_mrb_op08_result_20260705 import (
    _op08_from_op05,
)


def _assert_common_bodyfree_no_touch_no_promotion(material: dict[str, object]) -> None:
    assert material["source_mode"] == rdb.P7_R54_AHR_POST_MRB08_RDB_SOURCE_MODE
    assert material["git_connection_required"] is False
    assert material["git_checked"] is False
    assert material["body_free"] is True
    assert all(value is False for value in material["public_contract"].values())
    assert all(value is False for value in material["rdb_no_touch_contract"].values())
    assert all(value is False for value in material["body_free_markers"].values())
    assert all(value is False for value in material["not_claimed_boundary"].values())
    for key in rdb.P7_R54_AHR_POST_MRB08_RDB_REQUIRED_FALSE_FLAG_REFS:
        assert material[key] is False, key


def test_rdb_op00_refreezes_scope_no_touch_no_promotion_after_mrb_op08() -> None:
    material = rdb.build_p7_r54_ahr_post_mrb08_rdb_op00_scope_no_touch_no_promotion_refreeze_after_mrb_op08()

    assert set(material) == set(rdb.P7_R54_AHR_POST_MRB08_RDB_OP00_REQUIRED_FIELD_REFS)
    assert material["schema_version"] == rdb.P7_R54_AHR_POST_MRB08_RDB_OP00_SCHEMA_VERSION
    assert material["operation_step_ref"] == rdb.P7_R54_AHR_POST_MRB08_RDB_OP00_STEP_REF
    assert material["selected_stage_ref"] == rdb.P7_R54_AHR_POST_MRB08_RDB_SELECTED_STAGE_REF
    assert material["selected_design_target_ref"] == rdb.P7_R54_AHR_POST_MRB08_RDB_SELECTED_DESIGN_TARGET_REF
    assert material["boundary_prefix_ref"] == "RDB"
    assert material["boundary_prefix_meaning_ref"] == "Result Decision Boundary"
    assert material["source_mode_local_received_zip_only_confirmed"] is True
    assert material["github_connection_check_not_required_by_mash_instruction"] is True
    assert material["github_connection_check_performed"] is False
    assert material["rdb_op00_scope_confirmed"] is True
    assert material["rdb_op00_no_touch_boundary_confirmed"] is True
    assert material["rdb_op00_no_promotion_boundary_confirmed"] is True
    assert material["rdb_op00_does_not_intake_mrb_op08_result_memo"] is True
    assert material["rdb_op00_does_not_recall_dhr_op04"] is True
    assert material["rdb_op00_does_not_call_dhr_op05"] is True
    assert material["rdb_op00_does_not_call_dhr_op06"] is True
    assert material["rdb_op00_does_not_execute_dmd_r52_or_release"] is True
    assert material["rdb_op00_does_not_start_p5_p6_p8_p7_or_release"] is True
    assert material["rdb_op00_does_not_materialize_p8_question_spec"] is True
    assert material["implemented_steps"] == list(rdb.P7_R54_AHR_POST_MRB08_RDB_OP00_IMPLEMENTED_STEPS)
    assert material["not_yet_implemented_steps"] == list(rdb.P7_R54_AHR_POST_MRB08_RDB_OP00_NOT_YET_IMPLEMENTED_STEPS)
    assert material["next_required_step"] == rdb.P7_R54_AHR_POST_MRB08_RDB_OP01_STEP_REF
    assert rdb.assert_p7_r54_ahr_post_mrb08_rdb_op00_scope_no_touch_no_promotion_refreeze_after_mrb_op08_contract(material) is True
    _assert_common_bodyfree_no_touch_no_promotion(material)


@pytest.mark.parametrize(
    ("field", "bad_value"),
    [
        ("schema_version", "bad_schema"),
        ("source_mode", "github_remote"),
        ("git_checked", True),
        ("github_connection_check_performed", True),
        ("rdb_op00_no_touch_boundary_confirmed", False),
        ("rdb_op00_no_promotion_boundary_confirmed", False),
        ("rdb_op00_does_not_call_dhr_op05", False),
        ("rdb_op00_does_not_materialize_p8_question_spec", False),
        ("body_free", False),
        ("dhr_op05_called_here", True),
        ("dhr_op06_called_here", True),
        ("p8_start_allowed", True),
        ("release_allowed", True),
        ("next_required_step", rdb.P7_R54_AHR_POST_MRB08_RDB_OP02_STEP_REF),
    ],
)
def test_rdb_op00_contract_rejects_scope_touch_promotion_or_next_step_mutations(field: str, bad_value: object) -> None:
    material = rdb.build_p7_r54_ahr_post_mrb08_rdb_op00_scope_no_touch_no_promotion_refreeze_after_mrb_op08()
    material[field] = bad_value

    with pytest.raises(ValueError):
        rdb.assert_p7_r54_ahr_post_mrb08_rdb_op00_scope_no_touch_no_promotion_refreeze_after_mrb_op08_contract(material)


def test_rdb_op00_contract_rejects_public_contract_marker_mutation() -> None:
    material = rdb.build_p7_r54_ahr_post_mrb08_rdb_op00_scope_no_touch_no_promotion_refreeze_after_mrb_op08()
    material["public_contract"]["api_response_key_added"] = True

    with pytest.raises(ValueError):
        rdb.assert_p7_r54_ahr_post_mrb08_rdb_op00_scope_no_touch_no_promotion_refreeze_after_mrb_op08_contract(material)


def test_rdb_op00_contract_rejects_forbidden_top_level_body_payload_key() -> None:
    material = rdb.build_p7_r54_ahr_post_mrb08_rdb_op00_scope_no_touch_no_promotion_refreeze_after_mrb_op08()
    material["comment_text"] = "must never pass"

    with pytest.raises(ValueError):
        rdb.assert_p7_r54_ahr_post_mrb08_rdb_op00_scope_no_touch_no_promotion_refreeze_after_mrb_op08_contract(material)


def test_rdb_op01_accepts_valid_mrb_op08_bodyfree_closure_without_dhr_op05_call() -> None:
    mrb_op08 = _op08_from_op05(_op05_confirmed())
    material = rdb.build_p7_r54_ahr_post_mrb08_rdb_op01_mrb_op08_result_memo_closure_intake(
        mrb_op08_result_memo_closure=mrb_op08,
    )

    assert set(material) == set(rdb.P7_R54_AHR_POST_MRB08_RDB_OP01_REQUIRED_FIELD_REFS)
    assert material["schema_version"] == rdb.P7_R54_AHR_POST_MRB08_RDB_OP01_SCHEMA_VERSION
    assert material["operation_step_ref"] == rdb.P7_R54_AHR_POST_MRB08_RDB_OP01_STEP_REF
    assert material["op00_contract_valid"] is True
    assert material["mrb_op08_result_memo_present"] is True
    assert material["mrb_op08_contract_valid"] is True
    assert material["mrb_op08_status_ref"] == mrb.P7_R54_AHR_POST_DRI_MRB_OP08_STATUS_CLOSED_BODYFREE_STOPPED_REF
    assert material["bodyfree_result_memo_closure_status_ref"] == material["mrb_op08_status_ref"]
    assert material["mrb_op08_closed_bodyfree_stopped"] is True
    assert material["validation_summary_bodyfree_accepted"] is True
    assert material["result_memo_bodyfree_accepted"] is True
    assert material["mrb_selected_branch_ref"] == mrb.P7_R54_AHR_POST_DRI_MRB_STATUS_DHR_OP04_CONFIRMED_BODYFREE_STOPPED_REF
    assert material["dhr_op04_result_status_ref"] == dhr.P7_R54_AHR_POST_ELR19_DHR_OP04_STATUS_CONFIRMED_BODYFREE_REF
    assert material["actual_source_claim_confirmed_for_downstream_handoff"] is True
    assert material["rdb_op01_status_ref"] == rdb.P7_R54_AHR_POST_MRB08_RDB_OP01_STATUS_READY_FOR_OP02_REF
    assert material["rdb_op01_ready_for_rdb_op02"] is True
    assert material["rdb_op01_blocker_refs"] == []
    assert material["mrb_op08_input_forbidden_payload_key_path_refs"] == []
    assert material["mrb_op08_input_body_like_value_path_refs"] == []
    assert material["mrb_op08_input_promotion_claim_refs"] == []
    assert material["next_required_step"] == rdb.P7_R54_AHR_POST_MRB08_RDB_OP02_STEP_REF
    assert material["mrb_op08_closure_is_not_dhr_op05_call"] is True
    assert material["rdb_op01_does_not_classify_branch_status_consistency"] is True
    assert material["rdb_op01_does_not_materialize_branch_specific_manual_decision"] is True
    assert material["rdb_op01_does_not_call_dhr_op05"] is True
    assert material["dhr_op05_called_here"] is False
    assert material["dhr_op06_called_here"] is False
    assert material["dmd_execution_started_here"] is False
    assert material["r52_actual_execution_started_here"] is False
    assert material["p8_start_allowed"] is False
    assert material["p8_question_design_started"] is False
    assert material["release_allowed"] is False
    assert material["implemented_steps"] == list(rdb.P7_R54_AHR_POST_MRB08_RDB_OP01_IMPLEMENTED_STEPS)
    assert material["not_yet_implemented_steps"] == list(rdb.P7_R54_AHR_POST_MRB08_RDB_OP01_NOT_YET_IMPLEMENTED_STEPS)
    assert rdb.assert_p7_r54_ahr_post_mrb08_rdb_op01_mrb_op08_result_memo_closure_intake_contract(material) is True
    _assert_common_bodyfree_no_touch_no_promotion(material)


def test_rdb_op01_accepts_all_valid_mrb_op08_result_branches_but_does_not_classify_them_yet() -> None:
    expected = [
        (_op05_confirmed(), True),
        (_op05_not_confirmed(), False),
        (_op05_waiting_result(), False),
        (_op05_invalid_result(), False),
    ]
    for op05, confirmed in expected:
        mrb_op08 = _op08_from_op05(op05)
        material = rdb.build_p7_r54_ahr_post_mrb08_rdb_op01_mrb_op08_result_memo_closure_intake(
            mrb_op08_result_memo_closure=mrb_op08,
        )
        assert material["rdb_op01_status_ref"] == rdb.P7_R54_AHR_POST_MRB08_RDB_OP01_STATUS_READY_FOR_OP02_REF
        assert material["rdb_op01_ready_for_rdb_op02"] is True
        assert material["actual_source_claim_confirmed_for_downstream_handoff"] is confirmed
        assert material["rdb_op01_does_not_classify_branch_status_consistency"] is True
        assert material["rdb_op01_does_not_materialize_branch_specific_manual_decision"] is True
        assert material["rdb_op01_does_not_materialize_next_stage_candidate_envelope"] is True
        assert material["dhr_op05_called_here"] is False
        assert material["p8_question_design_started"] is False
        assert rdb.assert_p7_r54_ahr_post_mrb08_rdb_op01_mrb_op08_result_memo_closure_intake_contract(material) is True
        _assert_common_bodyfree_no_touch_no_promotion(material)


def test_rdb_op01_waits_when_mrb_op08_result_memo_is_missing() -> None:
    material = rdb.build_p7_r54_ahr_post_mrb08_rdb_op01_mrb_op08_result_memo_closure_intake()

    assert material["rdb_op01_status_ref"] == rdb.P7_R54_AHR_POST_MRB08_RDB_OP01_STATUS_WAITING_FOR_MRB08_CLOSURE_REF
    assert material["rdb_op01_waiting_for_mrb08_closure"] is True
    assert "mrb_op08_result_memo_closure_missing" in material["rdb_op01_blocker_refs"]
    assert material["next_required_step"] == rdb.P7_R54_AHR_POST_MRB08_RDB_NEXT_STEP_WAIT_FOR_MRB08_CLOSURE_REF
    assert material["dhr_op05_called_here"] is False
    assert rdb.assert_p7_r54_ahr_post_mrb08_rdb_op01_mrb_op08_result_memo_closure_intake_contract(material) is True
    _assert_common_bodyfree_no_touch_no_promotion(material)


def test_rdb_op01_waits_when_mrb_op08_is_waiting_for_result_memo_or_validation() -> None:
    waiting_mrb_op08 = _op08_from_op05(_op05_confirmed(), result_memo_bodyfree=None)
    material = rdb.build_p7_r54_ahr_post_mrb08_rdb_op01_mrb_op08_result_memo_closure_intake(
        mrb_op08_result_memo_closure=waiting_mrb_op08,
    )

    assert material["rdb_op01_status_ref"] == rdb.P7_R54_AHR_POST_MRB08_RDB_OP01_STATUS_WAITING_FOR_MRB08_CLOSURE_REF
    assert material["rdb_op01_waiting_for_mrb08_closure"] is True
    assert material["mrb_op08_waiting_for_op06_op07_or_validation"] is True
    assert "mrb_op08_waiting_for_op06_op07_or_validation" in material["rdb_op01_blocker_refs"]
    assert material["next_required_step"] == rdb.P7_R54_AHR_POST_MRB08_RDB_NEXT_STEP_WAIT_FOR_MRB08_CLOSURE_REF
    assert material["dhr_op05_called_here"] is False
    assert rdb.assert_p7_r54_ahr_post_mrb08_rdb_op01_mrb_op08_result_memo_closure_intake_contract(material) is True
    _assert_common_bodyfree_no_touch_no_promotion(material)


def test_rdb_op01_repairs_when_mrb_op08_contract_is_invalid() -> None:
    mrb_op08 = _op08_from_op05(_op05_confirmed())
    mrb_op08["schema_version"] = "bad_mrb_op08_schema"
    material = rdb.build_p7_r54_ahr_post_mrb08_rdb_op01_mrb_op08_result_memo_closure_intake(
        mrb_op08_result_memo_closure=mrb_op08,
    )

    assert material["rdb_op01_status_ref"] == rdb.P7_R54_AHR_POST_MRB08_RDB_OP01_STATUS_REPAIR_MRB08_INTAKE_REF
    assert material["rdb_op01_repair_required"] is True
    assert "mrb_op08_result_memo_closure_contract_invalid" in material["rdb_op01_blocker_refs"]
    assert material["next_required_step"] == rdb.P7_R54_AHR_POST_MRB08_RDB_NEXT_STEP_REPAIR_MRB08_INTAKE_REF
    assert material["dhr_op05_called_here"] is False
    assert rdb.assert_p7_r54_ahr_post_mrb08_rdb_op01_mrb_op08_result_memo_closure_intake_contract(material) is True
    _assert_common_bodyfree_no_touch_no_promotion(material)


def test_rdb_op01_blocks_body_payload_in_mrb_op08_without_copying_body_value() -> None:
    mrb_op08 = _op08_from_op05(_op05_confirmed())
    mrb_op08["result_memo_bodyfree_ref"]["question_text"] = "do not carry question body"
    material = rdb.build_p7_r54_ahr_post_mrb08_rdb_op01_mrb_op08_result_memo_closure_intake(
        mrb_op08_result_memo_closure=mrb_op08,
    )

    assert material["rdb_op01_status_ref"] == rdb.P7_R54_AHR_POST_MRB08_RDB_OP01_STATUS_BLOCKED_BODYFREE_PROMOTION_AUTORUN_REF
    assert material["rdb_op01_bodyfree_leak_promotion_or_autorun_blocked"] is True
    assert "mrb_op08_result_memo_closure.result_memo_bodyfree_ref.question_text" in material["mrb_op08_input_forbidden_payload_key_path_refs"]
    assert "mrb_op08_input_forbidden_payload_key_detected" in material["rdb_op01_blocker_refs"]
    assert material["next_required_step"] == rdb.P7_R54_AHR_POST_MRB08_RDB_NEXT_STEP_BLOCKED_MRB08_INTAKE_REF
    assert material["dhr_op05_called_here"] is False
    assert material["p8_question_design_started"] is False
    assert material["release_allowed"] is False
    assert "do not carry question body" not in repr(material)
    assert rdb.assert_p7_r54_ahr_post_mrb08_rdb_op01_mrb_op08_result_memo_closure_intake_contract(material) is True
    _assert_common_bodyfree_no_touch_no_promotion(material)


def test_rdb_op01_blocks_mrb_op08_downstream_promotion_claim_without_promoting_rdb() -> None:
    mrb_op08 = _op08_from_op05(_op05_confirmed())
    mrb_op08["dhr_op05_called_here"] = True
    mrb_op08["release_allowed"] = True
    material = rdb.build_p7_r54_ahr_post_mrb08_rdb_op01_mrb_op08_result_memo_closure_intake(
        mrb_op08_result_memo_closure=mrb_op08,
    )

    assert material["rdb_op01_status_ref"] == rdb.P7_R54_AHR_POST_MRB08_RDB_OP01_STATUS_BLOCKED_BODYFREE_PROMOTION_AUTORUN_REF
    assert material["rdb_op01_bodyfree_leak_promotion_or_autorun_blocked"] is True
    assert "mrb_op08_input_promotion_or_autorun_claim_detected" in material["rdb_op01_blocker_refs"]
    assert "mrb_op08_result_memo_closure.dhr_op05_called_here" in material["mrb_op08_input_promotion_claim_refs"]
    assert "mrb_op08_result_memo_closure.release_allowed" in material["mrb_op08_input_promotion_claim_refs"]
    assert material["dhr_op05_called_here"] is False
    assert material["release_allowed"] is False
    assert rdb.assert_p7_r54_ahr_post_mrb08_rdb_op01_mrb_op08_result_memo_closure_intake_contract(material) is True
    _assert_common_bodyfree_no_touch_no_promotion(material)


def test_rdb_op01_contract_rejects_promotion_or_next_step_mutations() -> None:
    material = rdb.build_p7_r54_ahr_post_mrb08_rdb_op01_mrb_op08_result_memo_closure_intake(
        mrb_op08_result_memo_closure=_op08_from_op05(_op05_confirmed()),
    )
    material["dhr_op05_called_here"] = True

    with pytest.raises(ValueError):
        rdb.assert_p7_r54_ahr_post_mrb08_rdb_op01_mrb_op08_result_memo_closure_intake_contract(material)


def test_rdb_op01_contract_rejects_ready_branch_with_blockers() -> None:
    material = rdb.build_p7_r54_ahr_post_mrb08_rdb_op01_mrb_op08_result_memo_closure_intake(
        mrb_op08_result_memo_closure=_op08_from_op05(_op05_confirmed()),
    )
    material["rdb_op01_blocker_refs"] = ["unexpected_blocker"]
    material["rdb_op01_blocker_ref_count"] = 1

    with pytest.raises(ValueError):
        rdb.assert_p7_r54_ahr_post_mrb08_rdb_op01_mrb_op08_result_memo_closure_intake_contract(material)


def test_rdb_op00_op01_full_title_aliases_match_short_builders_and_asserts() -> None:
    assert (
        rdb.build_p7_r54_ahr_post_mrb08_dhr_op04_result_manual_decision_rdb_op00_scope_no_touch_no_promotion_refreeze_after_mrb_op08
        is rdb.build_p7_r54_ahr_post_mrb08_rdb_op00_scope_no_touch_no_promotion_refreeze_after_mrb_op08
    )
    assert (
        rdb.assert_p7_r54_ahr_post_mrb08_dhr_op04_result_manual_decision_rdb_op00_scope_no_touch_no_promotion_refreeze_after_mrb_op08_contract
        is rdb.assert_p7_r54_ahr_post_mrb08_rdb_op00_scope_no_touch_no_promotion_refreeze_after_mrb_op08_contract
    )
    assert (
        rdb.build_p7_r54_ahr_post_mrb08_dhr_op04_result_manual_decision_rdb_op01_mrb_op08_result_memo_closure_intake
        is rdb.build_p7_r54_ahr_post_mrb08_rdb_op01_mrb_op08_result_memo_closure_intake
    )
    assert (
        rdb.assert_p7_r54_ahr_post_mrb08_dhr_op04_result_manual_decision_rdb_op01_mrb_op08_result_memo_closure_intake_contract
        is rdb.assert_p7_r54_ahr_post_mrb08_rdb_op01_mrb_op08_result_memo_closure_intake_contract
    )
