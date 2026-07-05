# -*- coding: utf-8 -*-
"""R54-AHR Post-DRI / DHR-OP04 manual re-intake MRB-OP00/OP01 tests."""

from __future__ import annotations

from copy import deepcopy
from pathlib import Path
import sys

import pytest

TEST_DIR = Path(__file__).resolve().parent
if str(TEST_DIR) not in sys.path:
    sys.path.insert(0, str(TEST_DIR))

import emlis_ai_p7_r54_ahr_post_dri_dhr_op04_manual_reintake_20260705 as mrb
import emlis_ai_p7_r54_ahr_post_rsr16_dhr_actual_source_claim_reintake_20260705 as dri
from test_r54_ahr_post_rsr16_dhr_actual_source_claim_reintake_dri_op10_op11_20260705 import (
    _op09_waiting_for_final_scan,
    _op10_ready,
)
from test_r54_ahr_post_rsr16_dhr_actual_source_claim_reintake_dri_op12_result_20260705 import (
    _op12_closed,
)


def _assert_common_bodyfree_no_touch_no_promotion(material: dict[str, object]) -> None:
    assert material["source_mode"] == mrb.P7_R54_AHR_POST_DRI_MRB_SOURCE_MODE
    assert material["git_connection_required"] is False
    assert material["git_checked"] is False
    assert material["body_free"] is True
    assert all(value is False for value in material["public_contract"].values())
    assert all(value is False for value in material["mrb_no_touch_contract"].values())
    assert all(value is False for value in material["body_free_markers"].values())
    assert all(value is False for value in material["not_claimed_boundary"].values())
    for key in mrb.P7_R54_AHR_POST_DRI_MRB_REQUIRED_FALSE_FLAG_REFS:
        assert material[key] is False


def _op10_waiting() -> dict[str, object]:
    material = dri.build_p7_r54_ahr_post_rsr16_dri_op10_deterministic_branch_resolver(
        dri_op09_dhr_op04_external_actual_source_claim_adapter_candidate=_op09_waiting_for_final_scan()
    )
    assert dri.assert_p7_r54_ahr_post_rsr16_dri_op10_deterministic_branch_resolver_contract(material) is True
    assert material["waiting_for_supplied_receipts_or_complete_candidate"] is True
    return material


def test_mrb_op00_refreezes_scope_no_touch_no_promotion() -> None:
    material = mrb.build_p7_r54_ahr_post_dri_mrb_op00_scope_no_touch_no_promotion_refreeze()

    assert set(material) == set(mrb.P7_R54_AHR_POST_DRI_MRB_OP00_REQUIRED_FIELD_REFS)
    assert material["schema_version"] == mrb.P7_R54_AHR_POST_DRI_MRB_OP00_SCHEMA_VERSION
    assert material["operation_step_ref"] == mrb.P7_R54_AHR_POST_DRI_MRB_OP00_STEP_REF
    assert material["selected_stage_ref"] == mrb.P7_R54_AHR_POST_DRI_MRB_SELECTED_STAGE_REF
    assert material["selected_design_target_ref"] == mrb.P7_R54_AHR_POST_DRI_MRB_SELECTED_DESIGN_TARGET_REF
    assert material["boundary_prefix_ref"] == "MRB"
    assert material["source_mode_local_received_zip_only_confirmed"] is True
    assert material["github_connection_check_not_required_by_mash_instruction"] is True
    assert material["github_connection_check_performed"] is False
    assert material["mrb_op00_scope_confirmed"] is True
    assert material["mrb_op00_no_touch_boundary_confirmed"] is True
    assert material["mrb_op00_no_promotion_boundary_confirmed"] is True
    assert material["mrb_op00_does_not_intake_dri_result_memo"] is True
    assert material["mrb_op00_does_not_extract_dri_op09_candidate"] is True
    assert material["mrb_op00_does_not_call_dhr_op04"] is True
    assert material["mrb_op00_does_not_execute_dhr_op05_dmd_r52_or_release"] is True
    assert material["mrb_op00_does_not_start_p5_p6_p8_p7_or_release"] is True
    assert material["implemented_steps"] == list(mrb.P7_R54_AHR_POST_DRI_MRB_OP00_IMPLEMENTED_STEPS)
    assert material["not_yet_implemented_steps"] == list(mrb.P7_R54_AHR_POST_DRI_MRB_OP00_NOT_YET_IMPLEMENTED_STEPS)
    assert material["next_required_step"] == mrb.P7_R54_AHR_POST_DRI_MRB_OP01_STEP_REF
    assert mrb.assert_p7_r54_ahr_post_dri_mrb_op00_scope_no_touch_no_promotion_refreeze_contract(material) is True
    _assert_common_bodyfree_no_touch_no_promotion(material)


@pytest.mark.parametrize(
    ("field", "bad_value"),
    [
        ("schema_version", "bad_schema"),
        ("source_mode", "github_remote"),
        ("git_checked", True),
        ("github_connection_check_performed", True),
        ("mrb_op00_no_touch_boundary_confirmed", False),
        ("mrb_op00_no_promotion_boundary_confirmed", False),
        ("mrb_op00_does_not_call_dhr_op04", False),
        ("body_free", False),
        ("dhr_op04_called_here", True),
        ("dhr_op05_called_here", True),
        ("p8_start_allowed", True),
        ("release_allowed", True),
        ("next_required_step", mrb.P7_R54_AHR_POST_DRI_MRB_OP02_STEP_REF),
    ],
)
def test_mrb_op00_contract_rejects_scope_touch_promotion_or_next_step_mutations(field: str, bad_value: object) -> None:
    material = mrb.build_p7_r54_ahr_post_dri_mrb_op00_scope_no_touch_no_promotion_refreeze()
    material[field] = bad_value

    with pytest.raises(ValueError):
        mrb.assert_p7_r54_ahr_post_dri_mrb_op00_scope_no_touch_no_promotion_refreeze_contract(material)


def test_mrb_op00_contract_rejects_public_contract_marker_mutation() -> None:
    material = mrb.build_p7_r54_ahr_post_dri_mrb_op00_scope_no_touch_no_promotion_refreeze()
    material["public_contract"]["api_response_key_added"] = True

    with pytest.raises(ValueError):
        mrb.assert_p7_r54_ahr_post_dri_mrb_op00_scope_no_touch_no_promotion_refreeze_contract(material)


def test_mrb_op00_contract_rejects_forbidden_top_level_body_payload_key() -> None:
    material = mrb.build_p7_r54_ahr_post_dri_mrb_op00_scope_no_touch_no_promotion_refreeze()
    material["comment_text"] = "must never pass"

    with pytest.raises(ValueError):
        mrb.assert_p7_r54_ahr_post_dri_mrb_op00_scope_no_touch_no_promotion_refreeze_contract(material)


def test_mrb_op01_accepts_dri_op12_closed_and_op10_ready_branch_without_dhr_op04_call() -> None:
    material = mrb.build_p7_r54_ahr_post_dri_mrb_op01_dri_result_memo_op10_branch_intake(
        dri_op12_result_memo_closure=_op12_closed(),
        dri_op10_deterministic_branch_resolver=_op10_ready(),
    )

    assert set(material) == set(mrb.P7_R54_AHR_POST_DRI_MRB_OP01_REQUIRED_FIELD_REFS)
    assert material["schema_version"] == mrb.P7_R54_AHR_POST_DRI_MRB_OP01_SCHEMA_VERSION
    assert material["operation_step_ref"] == mrb.P7_R54_AHR_POST_DRI_MRB_OP01_STEP_REF
    assert material["op00_contract_valid"] is True
    assert material["dri_op12_result_memo_present"] is True
    assert material["dri_op12_contract_valid"] is True
    assert material["dri_op12_status_ref"] == dri.P7_R54_AHR_POST_RSR16_DRI_OP12_STATUS_CLOSED_BODYFREE_REF
    assert material["dri_op12_result_memo_bodyfree_closed"] is True
    assert material["dri_op12_selected_dri_branch_is_ready_material_only"] is True
    assert material["dri_op10_branch_present"] is True
    assert material["dri_op10_contract_valid"] is True
    assert material["dri_op10_branch_ref"] == dri.P7_R54_AHR_POST_RSR16_DRI_BRANCH_READY_FOR_DHR_ACTUAL_SOURCE_CLAIM_REINTAKE_MATERIAL_NO_AUTO_EXECUTION_REF
    assert material["dri_op10_ready_for_dhr_material"] is True
    assert material["dri_op10_adapter_candidate_materialized"] is True
    assert material["dri_op10_adapter_candidate_for_manual_dhr_op04_input_only"] is True
    assert material["dri_op10_adapter_candidate_not_dhr_confirmed"] is True
    assert material["mrb_op01_status_ref"] == mrb.P7_R54_AHR_POST_DRI_MRB_OP01_STATUS_READY_FOR_OP02_REF
    assert material["mrb_op01_ready_for_mrb_op02"] is True
    assert material["mrb_op01_blocker_refs"] == []
    assert material["dri_input_forbidden_payload_key_path_refs"] == []
    assert material["dri_input_body_like_value_path_refs"] == []
    assert material["dri_input_promotion_claim_refs"] == []
    assert material["next_required_step"] == mrb.P7_R54_AHR_POST_DRI_MRB_OP02_STEP_REF
    assert material["dri_result_memo_closure_is_not_dhr_op04_call"] is True
    assert material["dri_result_memo_closure_is_not_dhr_actual_source_claim_confirmed"] is True
    assert material["mrb_op01_does_not_extract_dri_op09_candidate_body"] is True
    assert material["mrb_op01_does_not_call_dhr_op04"] is True
    assert material["dhr_op04_called_here"] is False
    assert material["dhr_actual_source_claim_confirmed_here"] is False
    assert material["dhr_actual_source_claim_reintake_executed_here"] is False
    assert material["dhr_op05_called_here"] is False
    assert material["dmd_execution_started_here"] is False
    assert material["r52_actual_execution_started_here"] is False
    assert material["p8_start_allowed"] is False
    assert material["p8_question_design_started"] is False
    assert material["release_allowed"] is False
    assert material["implemented_steps"] == list(mrb.P7_R54_AHR_POST_DRI_MRB_OP01_IMPLEMENTED_STEPS)
    assert material["not_yet_implemented_steps"] == list(mrb.P7_R54_AHR_POST_DRI_MRB_OP01_NOT_YET_IMPLEMENTED_STEPS)
    assert mrb.assert_p7_r54_ahr_post_dri_mrb_op01_dri_result_memo_op10_branch_intake_contract(material) is True
    _assert_common_bodyfree_no_touch_no_promotion(material)


def test_mrb_op01_waits_when_dri_op12_or_op10_material_is_missing() -> None:
    material = mrb.build_p7_r54_ahr_post_dri_mrb_op01_dri_result_memo_op10_branch_intake()

    assert material["mrb_op01_status_ref"] == mrb.P7_R54_AHR_POST_DRI_MRB_OP01_STATUS_WAITING_FOR_DRI_READY_REF
    assert material["mrb_op01_waiting_for_dri_ready_material"] is True
    assert "dri_op12_result_memo_missing" in material["mrb_op01_blocker_refs"]
    assert "dri_op10_branch_resolver_missing" in material["mrb_op01_blocker_refs"]
    assert material["next_required_step"] == mrb.P7_R54_AHR_POST_DRI_MRB_NEXT_STEP_WAIT_FOR_DRI_READY_MATERIAL_REF
    assert material["dhr_op04_called_here"] is False
    assert mrb.assert_p7_r54_ahr_post_dri_mrb_op01_dri_result_memo_op10_branch_intake_contract(material) is True
    _assert_common_bodyfree_no_touch_no_promotion(material)


def test_mrb_op01_waits_when_dri_op10_is_waiting_without_promotion() -> None:
    material = mrb.build_p7_r54_ahr_post_dri_mrb_op01_dri_result_memo_op10_branch_intake(
        dri_op12_result_memo_closure=_op12_closed(),
        dri_op10_deterministic_branch_resolver=_op10_waiting(),
    )

    assert material["mrb_op01_status_ref"] == mrb.P7_R54_AHR_POST_DRI_MRB_OP01_STATUS_WAITING_FOR_DRI_READY_REF
    assert material["mrb_op01_waiting_for_dri_ready_material"] is True
    assert material["dri_op10_waiting"] is True
    assert "dri_result_memo_or_op10_branch_waiting" in material["mrb_op01_blocker_refs"]
    assert material["next_required_step"] == mrb.P7_R54_AHR_POST_DRI_MRB_NEXT_STEP_WAIT_FOR_DRI_READY_MATERIAL_REF
    assert material["dhr_op04_called_here"] is False
    assert material["release_allowed"] is False
    assert mrb.assert_p7_r54_ahr_post_dri_mrb_op01_dri_result_memo_op10_branch_intake_contract(material) is True
    _assert_common_bodyfree_no_touch_no_promotion(material)


def test_mrb_op01_repairs_when_dri_op12_contract_is_invalid() -> None:
    op12 = _op12_closed()
    op12["schema_version"] = "bad_dri_op12_schema"
    material = mrb.build_p7_r54_ahr_post_dri_mrb_op01_dri_result_memo_op10_branch_intake(
        dri_op12_result_memo_closure=op12,
        dri_op10_deterministic_branch_resolver=_op10_ready(),
    )

    assert material["mrb_op01_status_ref"] == mrb.P7_R54_AHR_POST_DRI_MRB_OP01_STATUS_REPAIR_DRI_INTAKE_REF
    assert material["mrb_op01_repair_required"] is True
    assert "dri_op12_result_memo_contract_invalid" in material["mrb_op01_blocker_refs"]
    assert material["next_required_step"] == mrb.P7_R54_AHR_POST_DRI_MRB_NEXT_STEP_REPAIR_DRI_INTAKE_REF
    assert material["dhr_op04_called_here"] is False
    assert mrb.assert_p7_r54_ahr_post_dri_mrb_op01_dri_result_memo_op10_branch_intake_contract(material) is True
    _assert_common_bodyfree_no_touch_no_promotion(material)


def test_mrb_op01_repairs_when_dri_op10_contract_is_invalid() -> None:
    op10 = _op10_ready()
    op10["schema_version"] = "bad_dri_op10_schema"
    material = mrb.build_p7_r54_ahr_post_dri_mrb_op01_dri_result_memo_op10_branch_intake(
        dri_op12_result_memo_closure=_op12_closed(),
        dri_op10_deterministic_branch_resolver=op10,
    )

    assert material["mrb_op01_status_ref"] == mrb.P7_R54_AHR_POST_DRI_MRB_OP01_STATUS_REPAIR_DRI_INTAKE_REF
    assert material["mrb_op01_repair_required"] is True
    assert "dri_op10_branch_resolver_contract_invalid" in material["mrb_op01_blocker_refs"]
    assert material["next_required_step"] == mrb.P7_R54_AHR_POST_DRI_MRB_NEXT_STEP_REPAIR_DRI_INTAKE_REF
    assert material["dhr_op04_called_here"] is False
    assert mrb.assert_p7_r54_ahr_post_dri_mrb_op01_dri_result_memo_op10_branch_intake_contract(material) is True
    _assert_common_bodyfree_no_touch_no_promotion(material)


def test_mrb_op01_blocks_body_payload_in_dri_inputs_before_mrb_op02() -> None:
    op10 = _op10_ready()
    op10["question_text"] = "do not carry question body"
    material = mrb.build_p7_r54_ahr_post_dri_mrb_op01_dri_result_memo_op10_branch_intake(
        dri_op12_result_memo_closure=_op12_closed(),
        dri_op10_deterministic_branch_resolver=op10,
    )

    assert material["mrb_op01_status_ref"] == mrb.P7_R54_AHR_POST_DRI_MRB_OP01_STATUS_BLOCKED_BODYFREE_PROMOTION_AUTORUN_REF
    assert material["mrb_op01_bodyfree_leak_promotion_or_autorun_blocked"] is True
    assert "dri_op10_branch.question_text" in material["dri_input_forbidden_payload_key_path_refs"]
    assert "dri_input_forbidden_payload_key_detected" in material["mrb_op01_blocker_refs"]
    assert material["next_required_step"] == mrb.P7_R54_AHR_POST_DRI_MRB_NEXT_STEP_BLOCKED_DRI_INTAKE_REF
    assert material["dhr_op04_called_here"] is False
    assert material["p8_question_design_started"] is False
    assert material["release_allowed"] is False
    assert "do not carry question body" not in repr(material)
    assert mrb.assert_p7_r54_ahr_post_dri_mrb_op01_dri_result_memo_op10_branch_intake_contract(material) is True
    _assert_common_bodyfree_no_touch_no_promotion(material)


def test_mrb_op01_blocks_dri_promotion_claims_without_copying_them_as_mrb_claims() -> None:
    op12 = _op12_closed()
    op12["dhr_op04_called_by_dri_op12"] = True
    op12["release_allowed"] = True
    material = mrb.build_p7_r54_ahr_post_dri_mrb_op01_dri_result_memo_op10_branch_intake(
        dri_op12_result_memo_closure=op12,
        dri_op10_deterministic_branch_resolver=_op10_ready(),
    )

    assert material["mrb_op01_status_ref"] == mrb.P7_R54_AHR_POST_DRI_MRB_OP01_STATUS_BLOCKED_BODYFREE_PROMOTION_AUTORUN_REF
    assert material["mrb_op01_bodyfree_leak_promotion_or_autorun_blocked"] is True
    assert "dri_input_promotion_or_autorun_claim_detected" in material["mrb_op01_blocker_refs"]
    assert "dri_op12_result_memo.dhr_op04_called_by_dri_op12" in material["dri_input_promotion_claim_refs"]
    assert "dri_op12_result_memo.release_allowed" in material["dri_input_promotion_claim_refs"]
    assert material["dri_op12_dhr_op04_called"] is False
    assert material["dri_op12_release_allowed"] is False
    assert material["dhr_op04_called_here"] is False
    assert material["release_allowed"] is False
    assert mrb.assert_p7_r54_ahr_post_dri_mrb_op01_dri_result_memo_op10_branch_intake_contract(material) is True
    _assert_common_bodyfree_no_touch_no_promotion(material)


def test_mrb_op01_contract_rejects_branch_promotion_or_next_step_mutations() -> None:
    material = mrb.build_p7_r54_ahr_post_dri_mrb_op01_dri_result_memo_op10_branch_intake(
        dri_op12_result_memo_closure=_op12_closed(),
        dri_op10_deterministic_branch_resolver=_op10_ready(),
    )
    material["dhr_op04_called_here"] = True

    with pytest.raises(ValueError):
        mrb.assert_p7_r54_ahr_post_dri_mrb_op01_dri_result_memo_op10_branch_intake_contract(material)


def test_mrb_op01_contract_rejects_ready_branch_with_blockers() -> None:
    material = mrb.build_p7_r54_ahr_post_dri_mrb_op01_dri_result_memo_op10_branch_intake(
        dri_op12_result_memo_closure=_op12_closed(),
        dri_op10_deterministic_branch_resolver=_op10_ready(),
    )
    material["mrb_op01_blocker_refs"] = ["unexpected_blocker"]
    material["mrb_op01_blocker_ref_count"] = 1

    with pytest.raises(ValueError):
        mrb.assert_p7_r54_ahr_post_dri_mrb_op01_dri_result_memo_op10_branch_intake_contract(material)


def test_mrb_op00_op01_full_title_aliases_match_short_builders_and_asserts() -> None:
    assert (
        mrb.build_p7_r54_ahr_post_dri_dhr_op04_manual_reintake_mrb_op00_scope_no_touch_no_promotion_refreeze
        is mrb.build_p7_r54_ahr_post_dri_mrb_op00_scope_no_touch_no_promotion_refreeze
    )
    assert (
        mrb.assert_p7_r54_ahr_post_dri_dhr_op04_manual_reintake_mrb_op00_scope_no_touch_no_promotion_refreeze_contract
        is mrb.assert_p7_r54_ahr_post_dri_mrb_op00_scope_no_touch_no_promotion_refreeze_contract
    )
    assert (
        mrb.build_p7_r54_ahr_post_dri_dhr_op04_manual_reintake_mrb_op01_dri_result_memo_op10_branch_intake
        is mrb.build_p7_r54_ahr_post_dri_mrb_op01_dri_result_memo_op10_branch_intake
    )
    assert (
        mrb.assert_p7_r54_ahr_post_dri_dhr_op04_manual_reintake_mrb_op01_dri_result_memo_op10_branch_intake_contract
        is mrb.assert_p7_r54_ahr_post_dri_mrb_op01_dri_result_memo_op10_branch_intake_contract
    )
