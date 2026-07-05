# -*- coding: utf-8 -*-
"""R54-AHR Post-RSR16 DRI-OP02/OP03 OP15 alignment and inventory tests."""

from __future__ import annotations

from pathlib import Path
import sys

import pytest

TEST_DIR = Path(__file__).resolve().parent
if str(TEST_DIR) not in sys.path:
    sys.path.insert(0, str(TEST_DIR))

import emlis_ai_p7_r54_ahr_post_dhr09_actual_local_review_retry_start_decision_20260704 as rsr
import emlis_ai_p7_r54_ahr_post_rsr16_dhr_actual_source_claim_reintake_20260705 as dri
from test_r54_ahr_post_dhr09_actual_local_review_retry_start_decision_rsr_op14_op15_20260704 import (
    _rsr_op14_full_ready,
)
from test_r54_ahr_post_dhr09_actual_local_review_retry_start_decision_rsr_op16_result_20260704 import (
    _op15_complete_candidate,
    _op15_wait_for_allow,
    _op16_closed,
)


def _assert_common_bodyfree_no_touch_no_promotion(material: dict[str, object]) -> None:
    assert material["source_mode"] == dri.P7_R54_AHR_POST_RSR16_DRI_SOURCE_MODE
    assert material["git_connection_required"] is False
    assert material["git_checked"] is False
    assert material["body_free"] is True
    assert all(value is False for value in material["public_contract"].values())
    assert all(value is False for value in material["post_rsr16_no_touch_contract"].values())
    assert all(value is False for value in material["body_free_markers"].values())
    for key in dri.P7_R54_AHR_POST_RSR16_DRI_REQUIRED_FALSE_FLAG_REFS:
        assert material[key] is False
    assert all(value is False for value in material["not_claimed_boundary"].values())


def _op01_ready(op15: dict[str, object] | None = None) -> dict[str, object]:
    selected_op15 = op15 or _op15_complete_candidate()
    material = dri.build_p7_r54_ahr_post_rsr16_dri_op01_rsr_op16_result_memo_intake(
        rsr_op16_result_memo=_op16_closed(selected_op15),
    )
    assert dri.assert_p7_r54_ahr_post_rsr16_dri_op01_rsr_op16_result_memo_intake_contract(material) is True
    assert material["dri_op01_ready_for_rsr_op15_branch_alignment"] is True
    return material


def _op02_aligned(op15: dict[str, object] | None = None) -> dict[str, object]:
    selected_op15 = op15 or _op15_complete_candidate()
    material = dri.build_p7_r54_ahr_post_rsr16_dri_op02_rsr_op15_branch_next_step_alignment(
        rsr_op16_result_memo_intake=_op01_ready(selected_op15),
        rsr_op15_branch_resolver=selected_op15,
    )
    assert dri.assert_p7_r54_ahr_post_rsr16_dri_op02_rsr_op15_branch_next_step_alignment_contract(material) is True
    return material


def _op03_ready(op15: dict[str, object] | None = None, op14: dict[str, object] | None = None) -> dict[str, object]:
    selected_op15 = op15 or _op15_complete_candidate()
    selected_op14 = op14 or _rsr_op14_full_ready()
    material = dri.build_p7_r54_ahr_post_rsr16_dri_op03_complete_candidate_supplied_material_inventory(
        dri_op02_rsr_op15_branch_next_step_alignment=_op02_aligned(selected_op15),
        rsr_op15_branch_resolver=selected_op15,
        rsr_op14_final_validation=selected_op14,
    )
    assert dri.assert_p7_r54_ahr_post_rsr16_dri_op03_complete_candidate_supplied_material_inventory_contract(material) is True
    return material


def test_dri_op02_aligns_complete_candidate_branch_and_next_step_without_execution() -> None:
    material = _op02_aligned()

    assert set(material) == set(dri.P7_R54_AHR_POST_RSR16_DRI_OP02_REQUIRED_FIELD_REFS)
    assert material["schema_version"] == dri.P7_R54_AHR_POST_RSR16_DRI_OP02_SCHEMA_VERSION
    assert material["operation_step_ref"] == dri.P7_R54_AHR_POST_RSR16_DRI_OP02_STEP_REF
    assert material["op01_contract_valid"] is True
    assert material["op01_ready_for_rsr_op15_branch_alignment"] is True
    assert material["rsr_op15_contract_valid"] is True
    assert material["rsr_op15_branch_ref"] == dri.P7_R54_AHR_POST_RSR16_DRI_OP02_ACCEPTED_BRANCH_REF
    assert material["rsr_op15_next_required_step"] in dri.P7_R54_AHR_POST_RSR16_DRI_OP02_ACCEPTED_NEXT_REQUIRED_STEP_REFS
    assert material["rsr_op15_actual_evidence_complete_candidate"] is True
    assert material["dri_op02_status_ref"] == dri.P7_R54_AHR_POST_RSR16_DRI_OP02_STATUS_ALIGNED_REF
    assert material["rsr_op15_alignment_status_ref"] == material["dri_op02_status_ref"]
    assert material["dri_op02_aligned"] is True
    assert material["dri_op02_ready_for_complete_candidate_prerequisite_inventory"] is True
    assert material["dri_op02_blocker_refs"] == []
    assert material["dhr_op04_adapter_candidate_materialized_by_dri_op02"] is False
    assert material["dhr_op04_called_by_dri_op02"] is False
    assert material["dhr_actual_source_claim_reintake_executed_by_dri_op02"] is False
    assert material["rsr_op15_downstream_auto_execution_allowed"] is False
    assert material["p8_start_allowed"] is False
    assert material["release_allowed"] is False
    assert material["next_required_step"] == dri.P7_R54_AHR_POST_RSR16_DRI_OP03_STEP_REF
    _assert_common_bodyfree_no_touch_no_promotion(material)


def test_dri_op02_waits_when_op15_selected_branch_is_not_complete_candidate() -> None:
    op15 = _op15_wait_for_allow()
    material = dri.build_p7_r54_ahr_post_rsr16_dri_op02_rsr_op15_branch_next_step_alignment(
        rsr_op16_result_memo_intake=_op01_ready(op15),
        rsr_op15_branch_resolver=op15,
    )

    assert material["rsr_op15_contract_valid"] is True
    assert material["rsr_op15_branch_ref"] == rsr.P7_R54_AHR_POST_DHR09_RSR_OP15_BRANCH_WAIT_FOR_EXPLICIT_LOCAL_ONLY_ALLOW_REF
    assert material["dri_op02_status_ref"] == dri.P7_R54_AHR_POST_RSR16_DRI_OP02_STATUS_WAIT_FOR_COMPLETE_CANDIDATE_REF
    assert material["dri_op02_wait_for_rsr_op15_complete_candidate"] is True
    assert material["dri_op02_ready_for_complete_candidate_prerequisite_inventory"] is False
    assert material["next_required_step"] == dri.P7_R54_AHR_POST_RSR16_DRI_NEXT_STEP_WAIT_FOR_RSR_OP15_COMPLETE_CANDIDATE_REF
    assert dri.assert_p7_r54_ahr_post_rsr16_dri_op02_rsr_op15_branch_next_step_alignment_contract(material) is True
    _assert_common_bodyfree_no_touch_no_promotion(material)


@pytest.mark.parametrize(
    "branch_ref",
    [
        rsr.P7_R54_AHR_POST_DHR09_RSR_OP15_BRANCH_READY_TO_START_ACTUAL_LOCAL_ONLY_REVIEW_REF,
        rsr.P7_R54_AHR_POST_DHR09_RSR_OP15_BRANCH_REVIEW_IN_PROGRESS_OR_PAUSED_LOCAL_ONLY_REF,
        rsr.P7_R54_AHR_POST_DHR09_RSR_OP15_BRANCH_REVIEW_ABORTED_OR_INCOMPLETE_RETRY_REQUIRED_REF,
    ],
)
def test_dri_op02_waits_or_repairs_non_complete_candidate_retry_like_branches_without_promotion(branch_ref: str) -> None:
    op15 = dict(_op15_complete_candidate())
    op15["rsr_op15_branch_ref"] = branch_ref
    material = dri.build_p7_r54_ahr_post_rsr16_dri_op02_rsr_op15_branch_next_step_alignment(
        rsr_op16_result_memo_intake=_op01_ready(_op15_complete_candidate()),
        rsr_op15_branch_resolver=op15,
    )

    assert material["dri_op02_status_ref"] in {
        dri.P7_R54_AHR_POST_RSR16_DRI_OP02_STATUS_WAIT_FOR_COMPLETE_CANDIDATE_REF,
        dri.P7_R54_AHR_POST_RSR16_DRI_OP02_STATUS_REPAIR_BRANCH_NEXT_STEP_MISMATCH_REF,
    }
    assert material["dhr_op04_called_by_dri_op02"] is False
    assert material["dhr_actual_source_claim_reintake_executed_by_dri_op02"] is False
    assert material["p8_start_allowed"] is False
    assert material["release_allowed"] is False
    assert dri.assert_p7_r54_ahr_post_rsr16_dri_op02_rsr_op15_branch_next_step_alignment_contract(material) is True
    _assert_common_bodyfree_no_touch_no_promotion(material)


def test_dri_op02_repairs_when_complete_candidate_next_required_step_is_mismatched() -> None:
    op15 = dict(_op15_complete_candidate())
    op15["next_required_step"] = "start_p8_question_design"
    material = dri.build_p7_r54_ahr_post_rsr16_dri_op02_rsr_op15_branch_next_step_alignment(
        rsr_op16_result_memo_intake=_op01_ready(_op15_complete_candidate()),
        rsr_op15_branch_resolver=op15,
    )

    assert material["dri_op02_status_ref"] == dri.P7_R54_AHR_POST_RSR16_DRI_OP02_STATUS_REPAIR_BRANCH_NEXT_STEP_MISMATCH_REF
    assert material["dri_op02_repair_required"] is True
    assert material["dri_op02_ready_for_complete_candidate_prerequisite_inventory"] is False
    assert material["dri_op02_blocker_refs"] != []
    assert material["next_required_step"] == dri.P7_R54_AHR_POST_RSR16_DRI_NEXT_STEP_REPAIR_OP15_ALIGNMENT_REF
    assert dri.assert_p7_r54_ahr_post_rsr16_dri_op02_rsr_op15_branch_next_step_alignment_contract(material) is True
    _assert_common_bodyfree_no_touch_no_promotion(material)


def test_dri_op02_manual_holds_valid_op15_manual_hold_branch_without_downstream_promotion() -> None:
    op14 = dict(_rsr_op14_full_ready())
    op14["manual_hold_unresolved_no_promotion"] = True
    op15 = rsr.build_p7_r54_ahr_post_dhr09_rsr_op15_actual_evidence_complete_candidate_next_branch_resolver(
        final_validation=op14
    )
    assert rsr.assert_p7_r54_ahr_post_dhr09_rsr_op15_actual_evidence_complete_candidate_next_branch_resolver_contract(op15) is True
    material = dri.build_p7_r54_ahr_post_rsr16_dri_op02_rsr_op15_branch_next_step_alignment(
        rsr_op16_result_memo_intake=_op01_ready(_op15_complete_candidate()),
        rsr_op15_branch_resolver=op15,
    )

    assert material["rsr_op15_branch_ref"] == rsr.P7_R54_AHR_POST_DHR09_RSR_OP15_BRANCH_MANUAL_HOLD_UNRESOLVED_NO_PROMOTION_REF
    assert material["dri_op02_status_ref"] == dri.P7_R54_AHR_POST_RSR16_DRI_OP02_STATUS_MANUAL_HOLD_UNEXPECTED_BRANCH_REF
    assert material["dri_op02_manual_hold_unresolved_no_promotion"] is True
    assert material["next_required_step"] == dri.P7_R54_AHR_POST_RSR16_DRI_NEXT_STEP_MANUAL_HOLD_AFTER_OP02_REF
    assert material["dhr_op04_called_here"] is False
    assert material["release_allowed"] is False
    assert dri.assert_p7_r54_ahr_post_rsr16_dri_op02_rsr_op15_branch_next_step_alignment_contract(material) is True
    _assert_common_bodyfree_no_touch_no_promotion(material)


def test_dri_op02_blocks_body_leak_in_op15_without_leaking_the_body_value() -> None:
    op15 = dict(_op15_complete_candidate())
    op15["question_text"] = "this body-like value must never be returned"
    material = dri.build_p7_r54_ahr_post_rsr16_dri_op02_rsr_op15_branch_next_step_alignment(
        rsr_op16_result_memo_intake=_op01_ready(_op15_complete_candidate()),
        rsr_op15_branch_resolver=op15,
    )

    assert material["dri_op02_status_ref"] == dri.P7_R54_AHR_POST_RSR16_DRI_OP02_STATUS_BLOCKED_BODYFREE_LEAK_OR_PROMOTION_REF
    assert material["dri_op02_bodyfree_leak_or_promotion_blocked"] is True
    assert material["rsr_op15_forbidden_payload_key_path_refs"] != []
    assert material["dhr_op04_called_here"] is False
    assert material["p8_question_design_started"] is False
    assert "this body-like value" not in repr(material)
    assert dri.assert_p7_r54_ahr_post_rsr16_dri_op02_rsr_op15_branch_next_step_alignment_contract(material) is True
    _assert_common_bodyfree_no_touch_no_promotion(material)


def test_dri_op02_contract_rejects_execution_adapter_or_promotion_mutations() -> None:
    material = _op02_aligned()
    material["dhr_op04_adapter_candidate_materialized_by_dri_op02"] = True

    with pytest.raises(ValueError):
        dri.assert_p7_r54_ahr_post_rsr16_dri_op02_rsr_op15_branch_next_step_alignment_contract(material)


@pytest.mark.parametrize(
    ("field", "bad_value"),
    [
        ("schema_version", "bad_schema"),
        ("dri_op02_status_ref", dri.P7_R54_AHR_POST_RSR16_DRI_OP02_STATUS_WAIT_FOR_COMPLETE_CANDIDATE_REF),
        ("next_required_step", "call_dhr_op04_now"),
        ("dhr_op04_called_here", True),
        ("dhr_actual_source_claim_reintake_executed_here", True),
        ("p8_start_allowed", True),
        ("release_allowed", True),
        ("body_free", False),
    ],
)
def test_dri_op02_contract_rejects_field_mutations(field: str, bad_value: object) -> None:
    material = _op02_aligned()
    material[field] = bad_value

    with pytest.raises(ValueError):
        dri.assert_p7_r54_ahr_post_rsr16_dri_op02_rsr_op15_branch_next_step_alignment_contract(material)


def test_dri_op03_inventory_ready_with_complete_candidate_prerequisites_and_supplied_material_refs_only() -> None:
    material = _op03_ready()

    assert set(material) == set(dri.P7_R54_AHR_POST_RSR16_DRI_OP03_REQUIRED_FIELD_REFS)
    assert material["schema_version"] == dri.P7_R54_AHR_POST_RSR16_DRI_OP03_SCHEMA_VERSION
    assert material["operation_step_ref"] == dri.P7_R54_AHR_POST_RSR16_DRI_OP03_STEP_REF
    assert material["op02_contract_valid"] is True
    assert material["op02_aligned"] is True
    assert material["rsr_op15_contract_valid"] is True
    assert material["rsr_op15_actual_evidence_complete_candidate"] is True
    assert material["rsr_op14_contract_valid"] is True
    assert material["rsr_op14_final_validation_passed"] is True
    assert material["complete_candidate_prerequisite_refs"] == list(rsr.P7_R54_AHR_POST_DHR09_RSR_OP14_COMPLETE_CANDIDATE_PREREQUISITE_REFS)
    assert material["complete_candidate_prerequisite_missing_refs"] == []
    assert material["supplied_material_inventory_required_refs"] == list(dri.P7_R54_AHR_POST_RSR16_DRI_OP03_SUPPLIED_MATERIAL_REQUIRED_REFS)
    assert material["supplied_material_missing_refs"] == []
    assert material["dri_op03_status_ref"] == dri.P7_R54_AHR_POST_RSR16_DRI_OP03_STATUS_INVENTORY_READY_REF
    assert material["complete_candidate_inventory_status_ref"] == material["dri_op03_status_ref"]
    assert material["dri_op03_inventory_ready"] is True
    assert material["dri_op03_ready_for_actual_operation_receipt_revalidation"] is True
    assert material["rsr_op15_candidate_ref_alone_is_not_actual_evidence"] is True
    assert material["dhr_op04_adapter_candidate_materialized_by_dri_op03"] is False
    assert material["dhr_op04_called_by_dri_op03"] is False
    assert material["dhr_actual_source_claim_reintake_executed_by_dri_op03"] is False
    assert material["p8_question_design_started"] is False
    assert material["release_allowed"] is False
    assert material["next_required_step"] == dri.P7_R54_AHR_POST_RSR16_DRI_OP04_STEP_REF
    _assert_common_bodyfree_no_touch_no_promotion(material)


def test_dri_op03_does_not_accept_op15_candidate_ref_alone_as_supplied_inventory() -> None:
    op15 = _op15_complete_candidate()
    material = dri.build_p7_r54_ahr_post_rsr16_dri_op03_complete_candidate_supplied_material_inventory(
        dri_op02_rsr_op15_branch_next_step_alignment=_op02_aligned(op15),
        rsr_op15_branch_resolver=op15,
    )

    assert material["rsr_op15_actual_evidence_complete_candidate"] is True
    assert material["rsr_op14_final_validation_present"] is False
    assert material["rsr_op15_candidate_ref_alone_is_not_actual_evidence"] is True
    assert material["dri_op03_status_ref"] == dri.P7_R54_AHR_POST_RSR16_DRI_OP03_STATUS_WAIT_FOR_PREREQUISITES_OR_MATERIALS_REF
    assert material["dri_op03_wait_for_prerequisites_or_supplied_materials"] is True
    assert "rsr_op14_final_validation_material_missing" in material["dri_op03_blocker_refs"]
    assert material["supplied_material_missing_refs"] == [
        ref
        for ref in dri.P7_R54_AHR_POST_RSR16_DRI_OP03_SUPPLIED_MATERIAL_REQUIRED_REFS
        if ref != "rsr_op15_branch_resolver"
    ]
    assert material["dhr_op04_adapter_candidate_materialized_by_dri_op03"] is False
    assert material["next_required_step"] == dri.P7_R54_AHR_POST_RSR16_DRI_NEXT_STEP_WAIT_FOR_RSR_OP15_COMPLETE_CANDIDATE_REF
    assert dri.assert_p7_r54_ahr_post_rsr16_dri_op03_complete_candidate_supplied_material_inventory_contract(material) is True
    _assert_common_bodyfree_no_touch_no_promotion(material)


def test_dri_op03_waits_when_op02_is_not_aligned_to_complete_candidate() -> None:
    op15 = _op15_wait_for_allow()
    op02 = dri.build_p7_r54_ahr_post_rsr16_dri_op02_rsr_op15_branch_next_step_alignment(
        rsr_op16_result_memo_intake=_op01_ready(op15),
        rsr_op15_branch_resolver=op15,
    )
    material = dri.build_p7_r54_ahr_post_rsr16_dri_op03_complete_candidate_supplied_material_inventory(
        dri_op02_rsr_op15_branch_next_step_alignment=op02,
        rsr_op15_branch_resolver=op15,
        rsr_op14_final_validation=_rsr_op14_full_ready(),
    )

    assert material["op02_aligned"] is False
    assert material["dri_op03_status_ref"] == dri.P7_R54_AHR_POST_RSR16_DRI_OP03_STATUS_WAIT_FOR_PREREQUISITES_OR_MATERIALS_REF
    assert "dri_op02_not_aligned_for_inventory" in material["dri_op03_blocker_refs"]
    assert material["dhr_op04_called_here"] is False
    assert material["release_allowed"] is False
    assert dri.assert_p7_r54_ahr_post_rsr16_dri_op03_complete_candidate_supplied_material_inventory_contract(material) is True
    _assert_common_bodyfree_no_touch_no_promotion(material)


def test_dri_op03_repairs_present_but_invalid_or_incomplete_supplied_inventory() -> None:
    op14 = dict(_rsr_op14_full_ready())
    op14["actual_operation_receipt_accepted"] = False
    material = dri.build_p7_r54_ahr_post_rsr16_dri_op03_complete_candidate_supplied_material_inventory(
        dri_op02_rsr_op15_branch_next_step_alignment=_op02_aligned(),
        rsr_op15_branch_resolver=_op15_complete_candidate(),
        rsr_op14_final_validation=op14,
    )

    assert material["rsr_op14_final_validation_present"] is True
    assert material["dri_op03_status_ref"] in {
        dri.P7_R54_AHR_POST_RSR16_DRI_OP03_STATUS_WAIT_FOR_PREREQUISITES_OR_MATERIALS_REF,
        dri.P7_R54_AHR_POST_RSR16_DRI_OP03_STATUS_REPAIR_PREREQUISITES_OR_MATERIALS_REF,
    }
    assert "actual_operation_receipt_bodyfree_ref" in material["supplied_material_missing_refs"] or material["dri_op03_repair_required"] is True
    assert material["dhr_op04_adapter_candidate_materialized_by_dri_op03"] is False
    assert dri.assert_p7_r54_ahr_post_rsr16_dri_op03_complete_candidate_supplied_material_inventory_contract(material) is True
    _assert_common_bodyfree_no_touch_no_promotion(material)


def test_dri_op03_blocks_body_leak_in_supplied_material_without_leaking_the_body_value() -> None:
    op14 = dict(_rsr_op14_full_ready())
    op14["reviewer_free_text"] = "this reviewer body must not be returned"
    material = dri.build_p7_r54_ahr_post_rsr16_dri_op03_complete_candidate_supplied_material_inventory(
        dri_op02_rsr_op15_branch_next_step_alignment=_op02_aligned(),
        rsr_op15_branch_resolver=_op15_complete_candidate(),
        rsr_op14_final_validation=op14,
    )

    assert material["dri_op03_status_ref"] == dri.P7_R54_AHR_POST_RSR16_DRI_OP03_STATUS_BLOCKED_BODYFREE_LEAK_OR_PROMOTION_REF
    assert material["dri_op03_bodyfree_leak_or_promotion_blocked"] is True
    assert material["dri_op03_forbidden_payload_key_path_refs"] != []
    assert material["dhr_op04_called_by_dri_op03"] is False
    assert material["p8_question_design_started"] is False
    assert "this reviewer body" not in repr(material)
    assert dri.assert_p7_r54_ahr_post_rsr16_dri_op03_complete_candidate_supplied_material_inventory_contract(material) is True
    _assert_common_bodyfree_no_touch_no_promotion(material)


def test_dri_op03_contract_rejects_execution_adapter_or_promotion_mutations() -> None:
    material = _op03_ready()
    material["dhr_op04_adapter_candidate_materialized_by_dri_op03"] = True

    with pytest.raises(ValueError):
        dri.assert_p7_r54_ahr_post_rsr16_dri_op03_complete_candidate_supplied_material_inventory_contract(material)


@pytest.mark.parametrize(
    ("field", "bad_value"),
    [
        ("schema_version", "bad_schema"),
        ("dri_op03_status_ref", dri.P7_R54_AHR_POST_RSR16_DRI_OP03_STATUS_WAIT_FOR_PREREQUISITES_OR_MATERIALS_REF),
        ("next_required_step", "call_dhr_op04_now"),
        ("dhr_op04_called_here", True),
        ("dhr_actual_source_claim_reintake_executed_here", True),
        ("p8_question_design_started", True),
        ("release_allowed", True),
        ("body_free", False),
    ],
)
def test_dri_op03_contract_rejects_field_mutations(field: str, bad_value: object) -> None:
    material = _op03_ready()
    material[field] = bad_value

    with pytest.raises(ValueError):
        dri.assert_p7_r54_ahr_post_rsr16_dri_op03_complete_candidate_supplied_material_inventory_contract(material)


def test_dri_op02_op03_full_title_aliases_match_canonical_builders() -> None:
    op15 = _op15_complete_candidate()
    op01 = _op01_ready(op15)
    canonical_op02 = dri.build_p7_r54_ahr_post_rsr16_dri_op02_rsr_op15_branch_next_step_alignment(
        rsr_op16_result_memo_intake=op01,
        rsr_op15_branch_resolver=op15,
    )
    alias_op02 = dri.build_p7_r54_ahr_post_rsr16_dhr_actual_source_claim_reintake_dri_op02_rsr_op15_branch_next_step_alignment(
        rsr_op16_result_memo_intake=op01,
        rsr_op15_branch_resolver=op15,
    )
    assert canonical_op02 == alias_op02
    assert dri.assert_p7_r54_ahr_post_rsr16_dhr_actual_source_claim_reintake_dri_op02_rsr_op15_branch_next_step_alignment_contract(alias_op02) is True

    op14 = _rsr_op14_full_ready()
    canonical_op03 = dri.build_p7_r54_ahr_post_rsr16_dri_op03_complete_candidate_supplied_material_inventory(
        dri_op02_rsr_op15_branch_next_step_alignment=canonical_op02,
        rsr_op15_branch_resolver=op15,
        rsr_op14_final_validation=op14,
    )
    alias_op03 = dri.build_p7_r54_ahr_post_rsr16_dhr_actual_source_claim_reintake_dri_op03_complete_candidate_supplied_material_inventory(
        dri_op02_rsr_op15_branch_next_step_alignment=alias_op02,
        rsr_op15_branch_resolver=op15,
        rsr_op14_final_validation=op14,
    )
    assert canonical_op03 == alias_op03
    assert dri.assert_p7_r54_ahr_post_rsr16_dhr_actual_source_claim_reintake_dri_op03_complete_candidate_supplied_material_inventory_contract(alias_op03) is True
