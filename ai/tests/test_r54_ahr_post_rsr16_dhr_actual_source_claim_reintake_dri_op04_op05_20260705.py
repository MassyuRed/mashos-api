# -*- coding: utf-8 -*-
"""R54-AHR Post-RSR16 DRI-OP04/OP05 receipt and rows revalidation tests."""

from __future__ import annotations

from copy import deepcopy
from pathlib import Path
import sys

import pytest

TEST_DIR = Path(__file__).resolve().parent
if str(TEST_DIR) not in sys.path:
    sys.path.insert(0, str(TEST_DIR))

import emlis_ai_p7_r54_ahr_post_dhr09_actual_local_review_retry_start_decision_20260704 as rsr
import emlis_ai_p7_r54_ahr_post_rsr16_dhr_actual_source_claim_reintake_20260705 as dri
from test_r54_ahr_post_dhr09_actual_local_review_retry_start_decision_rsr_op10_op11_20260704 import (
    _rsr_op10_accepted,
    _valid_sanitized_and_rating_rows,
)
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


def _op03_ready() -> dict[str, object]:
    op15 = _op15_complete_candidate()
    op01 = dri.build_p7_r54_ahr_post_rsr16_dri_op01_rsr_op16_result_memo_intake(
        rsr_op16_result_memo=_op16_closed(op15),
    )
    assert dri.assert_p7_r54_ahr_post_rsr16_dri_op01_rsr_op16_result_memo_intake_contract(op01) is True
    op02 = dri.build_p7_r54_ahr_post_rsr16_dri_op02_rsr_op15_branch_next_step_alignment(
        rsr_op16_result_memo_intake=op01,
        rsr_op15_branch_resolver=op15,
    )
    assert dri.assert_p7_r54_ahr_post_rsr16_dri_op02_rsr_op15_branch_next_step_alignment_contract(op02) is True
    op03 = dri.build_p7_r54_ahr_post_rsr16_dri_op03_complete_candidate_supplied_material_inventory(
        dri_op02_rsr_op15_branch_next_step_alignment=op02,
        rsr_op15_branch_resolver=op15,
        rsr_op14_final_validation=_rsr_op14_full_ready(),
    )
    assert dri.assert_p7_r54_ahr_post_rsr16_dri_op03_complete_candidate_supplied_material_inventory_contract(op03) is True
    assert op03["dri_op03_ready_for_actual_operation_receipt_revalidation"] is True
    return op03


def _op03_waiting() -> dict[str, object]:
    op15 = _op15_wait_for_allow()
    op01 = dri.build_p7_r54_ahr_post_rsr16_dri_op01_rsr_op16_result_memo_intake(
        rsr_op16_result_memo=_op16_closed(op15),
    )
    op02 = dri.build_p7_r54_ahr_post_rsr16_dri_op02_rsr_op15_branch_next_step_alignment(
        rsr_op16_result_memo_intake=op01,
        rsr_op15_branch_resolver=op15,
    )
    op03 = dri.build_p7_r54_ahr_post_rsr16_dri_op03_complete_candidate_supplied_material_inventory(
        dri_op02_rsr_op15_branch_next_step_alignment=op02,
        rsr_op15_branch_resolver=op15,
        rsr_op14_final_validation=_rsr_op14_full_ready(),
    )
    assert dri.assert_p7_r54_ahr_post_rsr16_dri_op03_complete_candidate_supplied_material_inventory_contract(op03) is True
    assert op03["dri_op03_inventory_ready"] is False
    return op03


def _op04_ready(op10: dict[str, object] | None = None) -> dict[str, object]:
    material = dri.build_p7_r54_ahr_post_rsr16_dri_op04_actual_operation_receipt_revalidation(
        dri_op03_complete_candidate_supplied_material_inventory=_op03_ready(),
        rsr_op10_actual_operation_receipt_intake=op10 or _rsr_op10_accepted(),
    )
    assert dri.assert_p7_r54_ahr_post_rsr16_dri_op04_actual_operation_receipt_revalidation_contract(material) is True
    return material


def _op11_accepted(op10: dict[str, object] | None = None) -> dict[str, object]:
    selected_op10 = op10 or _rsr_op10_accepted()
    sanitized_rows, rating_rows, case_refs = _valid_sanitized_and_rating_rows(selected_op10)
    material = rsr.build_p7_r54_ahr_post_dhr09_rsr_op11_sanitized_review_result_rows_rating_rows_intake(
        actual_operation_receipt_intake=selected_op10,
        sanitized_review_result_rows=sanitized_rows,
        rating_rows=rating_rows,
        expected_case_refs=case_refs,
    )
    assert rsr.assert_p7_r54_ahr_post_dhr09_rsr_op11_sanitized_review_result_rows_rating_rows_intake_contract(material) is True
    return material


def _op05_ready(op04: dict[str, object] | None = None, op11: dict[str, object] | None = None) -> dict[str, object]:
    selected_op04 = op04 or _op04_ready()
    selected_op11 = op11 or _op11_accepted()
    material = dri.build_p7_r54_ahr_post_rsr16_dri_op05_sanitized_rows_rating_rows_revalidation(
        dri_op04_actual_operation_receipt_revalidation=selected_op04,
        rsr_op11_sanitized_review_result_rows_rating_rows_intake=selected_op11,
    )
    assert dri.assert_p7_r54_ahr_post_rsr16_dri_op05_sanitized_rows_rating_rows_revalidation_contract(material) is True
    return material


def test_dri_op04_revalidates_actual_operation_receipt_bodyfree_source_kind_person_without_execution() -> None:
    material = _op04_ready()

    assert set(material) == set(dri.P7_R54_AHR_POST_RSR16_DRI_OP04_REQUIRED_FIELD_REFS)
    assert material["schema_version"] == dri.P7_R54_AHR_POST_RSR16_DRI_OP04_SCHEMA_VERSION
    assert material["operation_step_ref"] == dri.P7_R54_AHR_POST_RSR16_DRI_OP04_STEP_REF
    assert material["op03_contract_valid"] is True
    assert material["op03_ready_for_actual_operation_receipt_revalidation"] is True
    assert material["rsr_op10_contract_valid"] is True
    assert material["rsr_op10_status_ref"] == rsr.P7_R54_AHR_POST_DHR09_RSR_OP10_STATUS_ACCEPTED_BODYFREE_REF
    assert material["rsr_op10_actual_operation_receipt_accepted"] is True
    assert material["actual_operation_receipt_accepted_by_rsr_op10"] is True
    assert material["source_kind_ref"] == rsr.P7_R54_AHR_POST_DHR09_RSR_ACTUAL_REVIEW_SOURCE_KIND_REF
    assert material["source_kind_is_actual_local_only_human_review_by_person"] is True
    assert material["created_from_real_operation"] is True
    assert material["actual_human_review_executed_by_person"] is True
    assert material["reviewed_case_count_is_24"] is True
    assert material["selection_row_count_is_24"] is True
    assert material["actual_operation_receipt_forbidden_payload_key_path_refs"] == []
    assert material["actual_operation_receipt_body_like_value_path_refs"] == []
    assert material["actual_operation_receipt_promotion_claim_refs"] == []
    assert material["dri_op04_status_ref"] == dri.P7_R54_AHR_POST_RSR16_DRI_OP04_STATUS_REVALIDATED_BODYFREE_REF
    assert material["actual_operation_receipt_revalidation_status_ref"] == material["dri_op04_status_ref"]
    assert material["dri_op04_revalidated_bodyfree"] is True
    assert material["dri_op04_ready_for_rows_and_ratings_revalidation"] is True
    assert material["dhr_op04_adapter_candidate_materialized_by_dri_op04"] is False
    assert material["dhr_op04_called_by_dri_op04"] is False
    assert material["dhr_actual_source_claim_reintake_executed_by_dri_op04"] is False
    assert material["actual_operation_receipt_created_here"] is False
    assert material["actual_review_evidence_complete_here"] is False
    assert material["p8_question_design_started"] is False
    assert material["release_allowed"] is False
    assert material["next_required_step"] == dri.P7_R54_AHR_POST_RSR16_DRI_OP05_STEP_REF
    _assert_common_bodyfree_no_touch_no_promotion(material)


def test_dri_op04_waits_for_missing_actual_operation_receipt_after_op03_ready() -> None:
    material = dri.build_p7_r54_ahr_post_rsr16_dri_op04_actual_operation_receipt_revalidation(
        dri_op03_complete_candidate_supplied_material_inventory=_op03_ready(),
    )

    assert material["rsr_op10_actual_operation_receipt_intake_present"] is False
    assert material["dri_op04_status_ref"] == dri.P7_R54_AHR_POST_RSR16_DRI_OP04_STATUS_WAIT_FOR_RECEIPT_REF
    assert material["dri_op04_wait_for_actual_operation_receipt"] is True
    assert material["dri_op04_ready_for_rows_and_ratings_revalidation"] is False
    assert material["next_required_step"] == dri.P7_R54_AHR_POST_RSR16_DRI_NEXT_STEP_WAIT_FOR_ACTUAL_OPERATION_RECEIPT_REF
    assert material["dhr_op04_called_here"] is False
    assert material["release_allowed"] is False
    assert dri.assert_p7_r54_ahr_post_rsr16_dri_op04_actual_operation_receipt_revalidation_contract(material) is True
    _assert_common_bodyfree_no_touch_no_promotion(material)


def test_dri_op04_waits_when_op03_inventory_is_not_ready() -> None:
    material = dri.build_p7_r54_ahr_post_rsr16_dri_op04_actual_operation_receipt_revalidation(
        dri_op03_complete_candidate_supplied_material_inventory=_op03_waiting(),
        rsr_op10_actual_operation_receipt_intake=_rsr_op10_accepted(),
    )

    assert material["op03_ready_for_actual_operation_receipt_revalidation"] is False
    assert material["dri_op04_status_ref"] == dri.P7_R54_AHR_POST_RSR16_DRI_OP04_STATUS_WAIT_FOR_RECEIPT_REF
    assert "dri_op03_inventory_not_ready" in material["dri_op04_blocker_refs"]
    assert material["dhr_actual_source_claim_reintake_executed_here"] is False
    assert dri.assert_p7_r54_ahr_post_rsr16_dri_op04_actual_operation_receipt_revalidation_contract(material) is True
    _assert_common_bodyfree_no_touch_no_promotion(material)


def test_dri_op04_repairs_contract_invalid_actual_operation_receipt_intake_without_promotion() -> None:
    op10 = dict(_rsr_op10_accepted())
    op10["schema_version"] = "wrong_schema"
    material = dri.build_p7_r54_ahr_post_rsr16_dri_op04_actual_operation_receipt_revalidation(
        dri_op03_complete_candidate_supplied_material_inventory=_op03_ready(),
        rsr_op10_actual_operation_receipt_intake=op10,
    )

    assert material["rsr_op10_contract_valid"] is False
    assert material["dri_op04_status_ref"] == dri.P7_R54_AHR_POST_RSR16_DRI_OP04_STATUS_REPAIR_RECEIPT_REF
    assert material["dri_op04_repair_required"] is True
    assert material["dri_op04_ready_for_rows_and_ratings_revalidation"] is False
    assert material["next_required_step"] == dri.P7_R54_AHR_POST_RSR16_DRI_NEXT_STEP_REPAIR_ACTUAL_OPERATION_RECEIPT_REF
    assert material["dhr_op04_called_here"] is False
    assert dri.assert_p7_r54_ahr_post_rsr16_dri_op04_actual_operation_receipt_revalidation_contract(material) is True
    _assert_common_bodyfree_no_touch_no_promotion(material)


@pytest.mark.parametrize(
    ("mutation", "expected_blocker", "leaked_text"),
    [
        ({"source_kind_ref": "helper_green"}, "actual_operation_receipt_source_kind_not_actual_local_only_human_review_by_person", None),
        ({"local_path": "/tmp/actual_review_packet.json"}, "dri_op04_forbidden_payload_key_detected", "/tmp/actual_review_packet.json"),
        ({"actual_operation_receipt_created_here": True}, "dri_op04_promotion_claim_detected", None),
    ],
)
def test_dri_op04_blocks_source_claim_path_or_promotion_without_leaking_values(mutation: dict[str, object], expected_blocker: str, leaked_text: str | None) -> None:
    op10 = dict(_rsr_op10_accepted())
    op10.update(mutation)
    material = dri.build_p7_r54_ahr_post_rsr16_dri_op04_actual_operation_receipt_revalidation(
        dri_op03_complete_candidate_supplied_material_inventory=_op03_ready(),
        rsr_op10_actual_operation_receipt_intake=op10,
    )

    assert material["dri_op04_status_ref"] == dri.P7_R54_AHR_POST_RSR16_DRI_OP04_STATUS_BLOCKED_RECEIPT_BODY_LEAK_OR_SOURCE_CLAIM_REF
    assert material["dri_op04_body_leak_or_source_claim_blocked"] is True
    assert expected_blocker in material["dri_op04_blocker_refs"]
    assert material["dhr_op04_called_by_dri_op04"] is False
    assert material["p8_start_allowed"] is False
    assert material["release_allowed"] is False
    if leaked_text:
        assert leaked_text not in repr(material)
    assert dri.assert_p7_r54_ahr_post_rsr16_dri_op04_actual_operation_receipt_revalidation_contract(material) is True
    _assert_common_bodyfree_no_touch_no_promotion(material)


def test_dri_op04_contract_rejects_adapter_execution_or_promotion_mutations() -> None:
    material = _op04_ready()
    material["dhr_op04_adapter_candidate_materialized_by_dri_op04"] = True

    with pytest.raises(ValueError):
        dri.assert_p7_r54_ahr_post_rsr16_dri_op04_actual_operation_receipt_revalidation_contract(material)


@pytest.mark.parametrize(
    ("field", "bad_value"),
    [
        ("schema_version", "bad_schema"),
        ("dri_op04_status_ref", dri.P7_R54_AHR_POST_RSR16_DRI_OP04_STATUS_WAIT_FOR_RECEIPT_REF),
        ("next_required_step", "call_dhr_op04_now"),
        ("dhr_op04_called_here", True),
        ("dhr_actual_source_claim_reintake_executed_here", True),
        ("p8_question_design_started", True),
        ("release_allowed", True),
        ("body_free", False),
    ],
)
def test_dri_op04_contract_rejects_field_mutations(field: str, bad_value: object) -> None:
    material = _op04_ready()
    material[field] = bad_value

    with pytest.raises(ValueError):
        dri.assert_p7_r54_ahr_post_rsr16_dri_op04_actual_operation_receipt_revalidation_contract(material)


def test_dri_op05_revalidates_24_sanitized_rows_and_24_rating_rows_without_question_or_dhr_execution() -> None:
    material = _op05_ready()

    assert set(material) == set(dri.P7_R54_AHR_POST_RSR16_DRI_OP05_REQUIRED_FIELD_REFS)
    assert material["schema_version"] == dri.P7_R54_AHR_POST_RSR16_DRI_OP05_SCHEMA_VERSION
    assert material["operation_step_ref"] == dri.P7_R54_AHR_POST_RSR16_DRI_OP05_STEP_REF
    assert material["op04_contract_valid"] is True
    assert material["op04_revalidated_bodyfree"] is True
    assert material["rsr_op11_contract_valid"] is True
    assert material["rsr_op11_status_ref"] == rsr.P7_R54_AHR_POST_DHR09_RSR_OP11_STATUS_ACCEPTED_BODYFREE_REF
    assert material["rsr_op11_sanitized_review_result_rows_accepted"] is True
    assert material["rsr_op11_rating_rows_accepted"] is True
    assert material["actual_review_rows_and_rating_rows_intaken_bodyfree"] is True
    assert material["sanitized_review_result_row_count"] == rsr.P7_R54_AHR_POST_DHR09_RSR_EXPECTED_CASE_COUNT
    assert material["rating_row_count"] == rsr.P7_R54_AHR_POST_DHR09_RSR_EXPECTED_CASE_COUNT
    assert material["sanitized_review_result_row_count_is_24"] is True
    assert material["rating_row_count_is_24"] is True
    assert material["rows_source_kind_is_actual_local_only_human_review_by_person"] is True
    assert material["sanitized_rows_bodyfree_only"] is True
    assert material["sanitized_rows_selection_only"] is True
    assert material["sanitized_rows_have_no_body_or_question_or_path_or_hash"] is True
    assert material["rating_rows_have_no_body_or_question_or_path_or_hash"] is True
    assert material["question_text_materialized"] is False
    assert material["p8_question_spec_created"] is False
    assert "sanitized_review_result_rows" not in material
    assert "rating_rows" not in material
    assert material["dri_op05_status_ref"] == dri.P7_R54_AHR_POST_RSR16_DRI_OP05_STATUS_ROWS_RATINGS_REVALIDATED_BODYFREE_REF
    assert material["rows_and_ratings_revalidation_status_ref"] == material["dri_op05_status_ref"]
    assert material["dri_op05_rows_and_ratings_revalidated_bodyfree"] is True
    assert material["dri_op05_ready_for_question_need_rows_bridge_only_revalidation"] is True
    assert material["dhr_op04_adapter_candidate_materialized_by_dri_op05"] is False
    assert material["dhr_op04_called_by_dri_op05"] is False
    assert material["dhr_actual_source_claim_reintake_executed_by_dri_op05"] is False
    assert material["actual_review_evidence_complete_here"] is False
    assert material["p8_question_design_started"] is False
    assert material["release_allowed"] is False
    assert material["next_required_step"] == dri.P7_R54_AHR_POST_RSR16_DRI_OP06_STEP_REF
    _assert_common_bodyfree_no_touch_no_promotion(material)


def test_dri_op05_waits_for_missing_rows_and_ratings_after_op04_ready() -> None:
    material = dri.build_p7_r54_ahr_post_rsr16_dri_op05_sanitized_rows_rating_rows_revalidation(
        dri_op04_actual_operation_receipt_revalidation=_op04_ready(),
    )

    assert material["rsr_op11_rows_rating_rows_intake_present"] is False
    assert material["dri_op05_status_ref"] == dri.P7_R54_AHR_POST_RSR16_DRI_OP05_STATUS_WAIT_FOR_ROWS_AND_RATINGS_REF
    assert material["dri_op05_wait_for_rows_and_ratings"] is True
    assert material["dri_op05_ready_for_question_need_rows_bridge_only_revalidation"] is False
    assert material["next_required_step"] == dri.P7_R54_AHR_POST_RSR16_DRI_NEXT_STEP_WAIT_FOR_ROWS_AND_RATINGS_REF
    assert material["dhr_op04_called_here"] is False
    assert dri.assert_p7_r54_ahr_post_rsr16_dri_op05_sanitized_rows_rating_rows_revalidation_contract(material) is True
    _assert_common_bodyfree_no_touch_no_promotion(material)


def test_dri_op05_waits_when_op04_receipt_revalidation_is_not_ready() -> None:
    op04 = dri.build_p7_r54_ahr_post_rsr16_dri_op04_actual_operation_receipt_revalidation(
        dri_op03_complete_candidate_supplied_material_inventory=_op03_ready(),
    )
    material = dri.build_p7_r54_ahr_post_rsr16_dri_op05_sanitized_rows_rating_rows_revalidation(
        dri_op04_actual_operation_receipt_revalidation=op04,
        rsr_op11_sanitized_review_result_rows_rating_rows_intake=_op11_accepted(),
    )

    assert material["op04_revalidated_bodyfree"] is False
    assert material["dri_op05_status_ref"] == dri.P7_R54_AHR_POST_RSR16_DRI_OP05_STATUS_WAIT_FOR_ROWS_AND_RATINGS_REF
    assert "dri_op04_receipt_revalidation_not_ready" in material["dri_op05_blocker_refs"]
    assert material["dhr_actual_source_claim_reintake_executed_here"] is False
    assert dri.assert_p7_r54_ahr_post_rsr16_dri_op05_sanitized_rows_rating_rows_revalidation_contract(material) is True
    _assert_common_bodyfree_no_touch_no_promotion(material)


def test_dri_op05_repairs_count_or_session_mismatch_without_promotion() -> None:
    op11 = dict(_op11_accepted())
    op11["sanitized_review_result_row_count"] = 23
    material = dri.build_p7_r54_ahr_post_rsr16_dri_op05_sanitized_rows_rating_rows_revalidation(
        dri_op04_actual_operation_receipt_revalidation=_op04_ready(),
        rsr_op11_sanitized_review_result_rows_rating_rows_intake=op11,
    )

    assert material["rsr_op11_contract_valid"] is False
    assert material["dri_op05_status_ref"] == dri.P7_R54_AHR_POST_RSR16_DRI_OP05_STATUS_REPAIR_ROWS_AND_RATINGS_REF
    assert material["dri_op05_repair_required"] is True
    assert material["dri_op05_ready_for_question_need_rows_bridge_only_revalidation"] is False
    assert material["next_required_step"] == dri.P7_R54_AHR_POST_RSR16_DRI_NEXT_STEP_REPAIR_ROWS_AND_RATINGS_REF
    assert material["dhr_op04_called_here"] is False
    assert material["release_allowed"] is False
    assert dri.assert_p7_r54_ahr_post_rsr16_dri_op05_sanitized_rows_rating_rows_revalidation_contract(material) is True
    _assert_common_bodyfree_no_touch_no_promotion(material)


@pytest.mark.parametrize(
    ("mutation", "expected_blocker", "leaked_text"),
    [
        ({"question_text": "do not materialize a question"}, "dri_op05_forbidden_payload_key_detected", "do not materialize a question"),
        ({"p8_question_spec_created": True}, "dri_op05_promotion_claim_detected", None),
        ({"rows_source_kind_is_actual_local_only_human_review_by_person": False}, "rows_source_kind_not_actual_local_only_human_review_by_person", None),
    ],
)
def test_dri_op05_blocks_body_question_materialization_or_source_claim_without_leaking_values(mutation: dict[str, object], expected_blocker: str, leaked_text: str | None) -> None:
    op11 = dict(_op11_accepted())
    op11.update(mutation)
    material = dri.build_p7_r54_ahr_post_rsr16_dri_op05_sanitized_rows_rating_rows_revalidation(
        dri_op04_actual_operation_receipt_revalidation=_op04_ready(),
        rsr_op11_sanitized_review_result_rows_rating_rows_intake=op11,
    )

    assert material["dri_op05_status_ref"] == dri.P7_R54_AHR_POST_RSR16_DRI_OP05_STATUS_BLOCKED_ROWS_BODY_LEAK_OR_SOURCE_CLAIM_REF
    assert material["dri_op05_body_leak_or_source_claim_blocked"] is True
    assert expected_blocker in material["dri_op05_blocker_refs"]
    assert material["dhr_op04_called_by_dri_op05"] is False
    assert material["p8_question_design_started"] is False
    assert material["release_allowed"] is False
    if leaked_text:
        assert leaked_text not in repr(material)
    assert dri.assert_p7_r54_ahr_post_rsr16_dri_op05_sanitized_rows_rating_rows_revalidation_contract(material) is True
    _assert_common_bodyfree_no_touch_no_promotion(material)


def test_dri_op05_contract_rejects_row_creation_question_materialization_or_promotion_mutations() -> None:
    material = _op05_ready()
    material["question_text_materialized"] = True

    with pytest.raises(ValueError):
        dri.assert_p7_r54_ahr_post_rsr16_dri_op05_sanitized_rows_rating_rows_revalidation_contract(material)


@pytest.mark.parametrize(
    ("field", "bad_value"),
    [
        ("schema_version", "bad_schema"),
        ("dri_op05_status_ref", dri.P7_R54_AHR_POST_RSR16_DRI_OP05_STATUS_WAIT_FOR_ROWS_AND_RATINGS_REF),
        ("next_required_step", "call_dhr_op04_now"),
        ("dhr_op04_called_here", True),
        ("dhr_actual_source_claim_reintake_executed_here", True),
        ("p8_question_design_started", True),
        ("release_allowed", True),
        ("body_free", False),
    ],
)
def test_dri_op05_contract_rejects_field_mutations(field: str, bad_value: object) -> None:
    material = _op05_ready()
    material[field] = bad_value

    with pytest.raises(ValueError):
        dri.assert_p7_r54_ahr_post_rsr16_dri_op05_sanitized_rows_rating_rows_revalidation_contract(material)


def test_dri_op04_op05_full_title_aliases_match_canonical_builders() -> None:
    op10 = _rsr_op10_accepted()
    op03 = _op03_ready()
    canonical_op04 = dri.build_p7_r54_ahr_post_rsr16_dri_op04_actual_operation_receipt_revalidation(
        dri_op03_complete_candidate_supplied_material_inventory=op03,
        rsr_op10_actual_operation_receipt_intake=op10,
    )
    alias_op04 = dri.build_p7_r54_ahr_post_rsr16_dhr_actual_source_claim_reintake_dri_op04_actual_operation_receipt_revalidation(
        dri_op03_complete_candidate_supplied_material_inventory=op03,
        rsr_op10_actual_operation_receipt_intake=op10,
    )
    assert canonical_op04 == alias_op04
    assert dri.assert_p7_r54_ahr_post_rsr16_dhr_actual_source_claim_reintake_dri_op04_actual_operation_receipt_revalidation_contract(alias_op04) is True

    op11 = _op11_accepted(op10)
    canonical_op05 = dri.build_p7_r54_ahr_post_rsr16_dri_op05_sanitized_rows_rating_rows_revalidation(
        dri_op04_actual_operation_receipt_revalidation=canonical_op04,
        rsr_op11_sanitized_review_result_rows_rating_rows_intake=op11,
    )
    alias_op05 = dri.build_p7_r54_ahr_post_rsr16_dhr_actual_source_claim_reintake_dri_op05_sanitized_rows_rating_rows_revalidation(
        dri_op04_actual_operation_receipt_revalidation=alias_op04,
        rsr_op11_sanitized_review_result_rows_rating_rows_intake=op11,
    )
    assert canonical_op05 == alias_op05
    assert dri.assert_p7_r54_ahr_post_rsr16_dhr_actual_source_claim_reintake_dri_op05_sanitized_rows_rating_rows_revalidation_contract(alias_op05) is True
