# -*- coding: utf-8 -*-
"""R54-AHR Post-DHR09 RSR-OP12/OP13 bridge-row and purge-receipt intake tests."""

from __future__ import annotations

from copy import deepcopy
from pathlib import Path
import sys

import pytest

TEST_DIR = Path(__file__).resolve().parent
if str(TEST_DIR) not in sys.path:
    sys.path.insert(0, str(TEST_DIR))

import emlis_ai_p7_r54_ahr_post_dhr09_actual_local_review_retry_start_decision_20260704 as rsr
from test_r54_ahr_post_dhr09_actual_local_review_retry_start_decision_rsr_op02_op03_20260704 import (
    _assert_common_bodyfree_no_touch_no_promotion,
)
from test_r54_ahr_post_dhr09_actual_local_review_retry_start_decision_rsr_op10_op11_20260704 import (
    _rsr_op10_accepted,
    _valid_sanitized_and_rating_rows,
)


def _rsr_op11_accepted() -> dict[str, object]:
    op10 = _rsr_op10_accepted()
    sanitized_rows, rating_rows, case_refs = _valid_sanitized_and_rating_rows(op10)
    material = rsr.build_p7_r54_ahr_post_dhr09_rsr_op11_sanitized_review_result_rows_rating_rows_intake(
        actual_operation_receipt_intake=op10,
        sanitized_review_result_rows=sanitized_rows,
        rating_rows=rating_rows,
        expected_case_refs=case_refs,
    )
    assert rsr.assert_p7_r54_ahr_post_dhr09_rsr_op11_sanitized_review_result_rows_rating_rows_intake_contract(material) is True
    assert material["rsr_op11_sanitized_review_result_rows_accepted"] is True
    assert material["rsr_op11_rating_rows_accepted"] is True
    assert material["question_need_observation_rows_required_next"] is True
    return material


def _valid_question_need_observation_rows(op11: dict[str, object] | None = None) -> list[dict[str, object]]:
    op11 = op11 or _rsr_op11_accepted()
    sanitized_rows = list(op11["sanitized_review_result_rows"])
    rating_rows = list(op11["rating_rows"])
    rating_by_case = {row["case_ref"]: row for row in rating_rows}
    rows: list[dict[str, object]] = []
    for index, sanitized in enumerate(sanitized_rows, start=1):
        rating = rating_by_case[sanitized["case_ref"]]
        rows.append({
            "schema_version": rsr.P7_R54_AHR_POST_DHR09_RSR_QUESTION_NEED_OBSERVATION_ROW_SCHEMA_VERSION,
            "question_need_observation_row_ref": f"question_need_observation_row_ref_{index:03d}",
            "review_session_id": op11["review_session_id"],
            "operation_receipt_ref": op11["operation_receipt_ref"],
            "source_sanitized_review_result_row_ref": sanitized["review_result_row_ref"],
            "source_rating_row_ref": rating["rating_row_ref"],
            "case_ref": sanitized["case_ref"],
            "reviewer_person_ref": op11["reviewer_person_ref"],
            "source_kind_ref": rsr.P7_R54_AHR_POST_DHR09_RSR_ACTUAL_REVIEW_SOURCE_KIND_REF,
            "question_need_primary_class_ref": sanitized["question_need_primary_class_ref"],
            "ambiguity_kind_refs": list(sanitized["ambiguity_kind_refs"]),
            "one_question_fit_ref": sanitized["one_question_fit_ref"],
            "p7_p8_bridge_material_only": True,
            "p8_design_material_candidate_only": True,
            "question_observation_material_only": True,
            "question_text_materialized": False,
            "draft_question_text_materialized": False,
            "p8_question_spec_created": False,
            "p8_question_design_started": False,
            "row_created_by_helper": False,
            "row_created_for_unit_test": False,
            "row_is_synthetic_contract_fixture": False,
            "historical_row_reused": False,
            "body_free": True,
        })
    return rows


def _rsr_op12_accepted() -> dict[str, object]:
    op11 = _rsr_op11_accepted()
    material = rsr.build_p7_r54_ahr_post_dhr09_rsr_op12_question_need_observation_rows_intake_p7_p8_bridge_material_only(
        review_rows_rating_rows_intake=op11,
        question_need_observation_rows=_valid_question_need_observation_rows(op11),
    )
    assert rsr.assert_p7_r54_ahr_post_dhr09_rsr_op12_question_need_observation_rows_intake_p7_p8_bridge_material_only_contract(material) is True
    assert material["rsr_op12_question_need_observation_rows_accepted"] is True
    assert material["disposal_purge_receipt_required_next"] is True
    return material


def _valid_disposal_purge_receipt(op12: dict[str, object] | None = None) -> dict[str, object]:
    op12 = op12 or _rsr_op12_accepted()
    return {
        "schema_version": rsr.P7_R54_AHR_POST_DHR09_RSR_DISPOSAL_PURGE_RECEIPT_SCHEMA_VERSION,
        "disposal_purge_receipt_ref": "disposal_purge_receipt_bodyfree_ref_001",
        "review_session_id": op12["review_session_id"],
        "operation_receipt_ref": op12["operation_receipt_ref"],
        "packet_request_ref": op12["operation_receipt_packet_request_ref"],
        "source_kind_ref": rsr.P7_R54_AHR_POST_DHR09_RSR_ACTUAL_REVIEW_SOURCE_KIND_REF,
        "body_full_packet_retained": False,
        "local_temp_material_retained": False,
        "reviewer_working_form_body_retained": False,
        "external_export_performed": False,
        "purge_completed": True,
        "raw_input_included": False,
        "comment_text_body_included": False,
        "returned_surface_body_included": False,
        "reviewer_free_text_included": False,
        "reviewer_note_body_included": False,
        "question_text_included": False,
        "draft_question_text_included": False,
        "answer_text_included": False,
        "local_path_included": False,
        "body_hash_included": False,
        "terminal_output_body_included": False,
        "body_free": True,
    }


def _assert_op12_no_question_or_promotion(material: dict[str, object]) -> None:
    assert material["rsr_op12_does_not_create_question_need_rows"] is True
    assert material["rsr_op12_does_not_materialize_question_text_or_p8_spec"] is True
    assert material["rsr_op12_does_not_execute_disposal_purge"] is True
    assert material["question_text_materialized"] is False
    assert material["draft_question_text_materialized"] is False
    assert material["p8_question_spec_created"] is False
    assert material["p8_question_design_started_here"] is False
    assert material["p8_question_design_started_by_rows"] is False
    assert material["actual_review_evidence_complete_here"] is False
    assert material["actual_question_need_observation_rows_materialized_here"] is False
    assert material["actual_disposal_purge_executed_here"] is False
    assert material["dmd_execution_started_here"] is False
    assert material["r52_actual_execution_started_here"] is False
    assert material["p8_start_allowed"] is False
    assert material["p8_question_design_started"] is False
    assert material["p7_complete"] is False
    assert material["release_allowed"] is False


def _assert_op13_no_purge_execution_or_completion(material: dict[str, object]) -> None:
    assert material["helper_executes_disposal_purge"] is False
    assert material["actual_disposal_purge_executed_here_by_helper"] is False
    assert material["rsr_op13_does_not_execute_disposal_purge"] is True
    assert material["rsr_op13_does_not_perform_final_no_leak_validation"] is True
    assert material["rsr_op13_does_not_complete_actual_evidence"] is True
    assert material["actual_review_evidence_complete_here"] is False
    assert material["actual_disposal_purge_executed_here"] is False
    assert material["dmd_execution_started_here"] is False
    assert material["r52_actual_execution_started_here"] is False
    assert material["p8_start_allowed"] is False
    assert material["p8_question_design_started"] is False
    assert material["p7_complete"] is False
    assert material["release_allowed"] is False


def test_rsr_op12_waits_for_question_need_observation_rows_after_op11_without_creating_rows() -> None:
    material = rsr.build_p7_r54_ahr_post_dhr09_rsr_op12_question_need_observation_rows_intake_p7_p8_bridge_material_only(
        review_rows_rating_rows_intake=_rsr_op11_accepted(),
    )

    assert set(material) == set(rsr.P7_R54_AHR_POST_DHR09_RSR_OP12_REQUIRED_FIELD_REFS)
    assert material["schema_version"] == rsr.P7_R54_AHR_POST_DHR09_RSR_OP12_SCHEMA_VERSION
    assert material["operation_step_ref"] == rsr.P7_R54_AHR_POST_DHR09_RSR_OP12_STEP_REF
    assert material["rsr_op12_status_ref"] == rsr.P7_R54_AHR_POST_DHR09_RSR_OP12_STATUS_MISSING_WAITING_REF
    assert material["rsr_op12_question_need_observation_rows_missing_waiting"] is True
    assert material["rsr_op12_question_need_observation_rows_accepted"] is False
    assert material["disposal_purge_receipt_required_next"] is False
    assert material["next_required_step"] == rsr.P7_R54_AHR_POST_DHR09_RSR_NEXT_STEP_PROVIDE_QUESTION_NEED_OBSERVATION_ROWS_BODYFREE_REF
    assert rsr.assert_p7_r54_ahr_post_dhr09_rsr_op12_question_need_observation_rows_intake_p7_p8_bridge_material_only_contract(material) is True
    _assert_common_bodyfree_no_touch_no_promotion(material)
    _assert_op12_no_question_or_promotion(material)


def test_rsr_op12_accepts_question_need_observation_rows_as_p7_p8_bridge_material_only() -> None:
    op11 = _rsr_op11_accepted()
    material = rsr.build_p7_r54_ahr_post_dhr09_rsr_op12_question_need_observation_rows_intake_p7_p8_bridge_material_only(
        review_rows_rating_rows_intake=op11,
        question_need_observation_rows=_valid_question_need_observation_rows(op11),
    )

    assert material["rsr_op12_status_ref"] == rsr.P7_R54_AHR_POST_DHR09_RSR_OP12_STATUS_ACCEPTED_BODYFREE_REF
    assert material["question_need_observation_row_count"] == rsr.P7_R54_AHR_POST_DHR09_RSR_EXPECTED_CASE_COUNT
    assert material["question_need_observation_row_count_is_24"] is True
    assert material["question_need_rows_match_op11_case_refs"] is True
    assert material["question_need_observation_rows_bodyfree_only"] is True
    assert material["question_need_observation_rows_from_review_rows_and_rating_rows"] is True
    assert material["question_need_observation_rows_have_actual_person_source"] is True
    assert material["question_need_observation_rows_have_allowed_classes"] is True
    assert material["question_need_observation_rows_material_only"] is True
    assert material["question_need_observation_rows_have_no_question_text_or_p8_spec"] is True
    assert material["p7_p8_bridge_material_only"] is True
    assert material["p8_design_material_candidate_only"] is True
    assert material["question_observation_material_only"] is True
    assert material["p8_question_spec_created"] is False
    assert material["p8_question_design_started_here"] is False
    assert material["disposal_purge_receipt_required_next"] is True
    assert material["next_required_step"] == rsr.P7_R54_AHR_POST_DHR09_RSR_OP13_STEP_REF
    assert rsr.assert_p7_r54_ahr_post_dhr09_rsr_op12_question_need_observation_rows_intake_p7_p8_bridge_material_only_contract(material) is True
    _assert_common_bodyfree_no_touch_no_promotion(material)
    _assert_op12_no_question_or_promotion(material)


@pytest.mark.parametrize(
    ("mutator", "expected_blocker"),
    [
        (lambda rows: rows.__setitem__(0, {**rows[0], "question_text": "do not leak this draft question"}), "question_need_observation_rows_forbidden_payload_key_detected"),
        (lambda rows: rows[0].__setitem__("question_text_materialized", True), "question_need_observation_row_question_text_materialized_not_false"),
        (lambda rows: rows[0].__setitem__("p8_question_spec_created", True), "question_need_observation_row_p8_question_spec_created_not_false"),
        (lambda rows: rows[0].__setitem__("p8_question_design_started", True), "question_need_observation_row_p8_question_design_started_not_false"),
        (lambda rows: rows[0].__setitem__("row_created_by_helper", True), "question_need_observation_row_row_created_by_helper_not_false"),
        (lambda rows: rows[0].__setitem__("source_kind_ref", "unit_test_fixture_not_actual"), "question_need_observation_row_source_kind_not_actual_local_only_human_review_by_person"),
    ],
)
def test_rsr_op12_blocks_or_repairs_question_need_rows_with_body_text_p8_materialization_or_source_claim(mutator, expected_blocker: str) -> None:
    op11 = _rsr_op11_accepted()
    rows = _valid_question_need_observation_rows(op11)
    mutator(rows)
    material = rsr.build_p7_r54_ahr_post_dhr09_rsr_op12_question_need_observation_rows_intake_p7_p8_bridge_material_only(
        review_rows_rating_rows_intake=op11,
        question_need_observation_rows=rows,
    )

    assert material["rsr_op12_question_need_observation_rows_accepted"] is False
    assert expected_blocker in material["op12_blocker_refs"]
    assert material["actual_question_need_observation_rows_intaken_bodyfree"] is False
    assert material["disposal_purge_receipt_required_next"] is False
    assert "do not leak this draft question" not in repr(material)
    assert rsr.assert_p7_r54_ahr_post_dhr09_rsr_op12_question_need_observation_rows_intake_p7_p8_bridge_material_only_contract(material) is True
    _assert_common_bodyfree_no_touch_no_promotion(material)
    _assert_op12_no_question_or_promotion(material)


@pytest.mark.parametrize(
    ("field", "bad_value"),
    [
        ("question_need_observation_rows_accepted_by_rsr_op12", False),
        ("rsr_op12_does_not_create_question_need_rows", False),
        ("rsr_op12_does_not_materialize_question_text_or_p8_spec", False),
        ("question_text_materialized", True),
        ("draft_question_text_materialized", True),
        ("p8_question_spec_created", True),
        ("p8_question_design_started_here", True),
        ("actual_question_need_observation_rows_materialized_here", True),
        ("actual_review_evidence_complete_here", True),
        ("p8_start_allowed", True),
        ("p8_question_design_started", True),
        ("release_allowed", True),
        ("next_required_step", rsr.P7_R54_AHR_POST_DHR09_RSR_OP14_STEP_REF),
    ],
)
def test_rsr_op12_contract_rejects_question_row_creation_p8_or_promotion_mutations(field: str, bad_value: object) -> None:
    material = _rsr_op12_accepted()
    material[field] = bad_value

    with pytest.raises(ValueError):
        rsr.assert_p7_r54_ahr_post_dhr09_rsr_op12_question_need_observation_rows_intake_p7_p8_bridge_material_only_contract(material)


def test_rsr_op13_waits_for_disposal_purge_receipt_after_op12_without_executing_purge() -> None:
    material = rsr.build_p7_r54_ahr_post_dhr09_rsr_op13_disposal_purge_receipt_intake(
        question_need_observation_rows_intake=_rsr_op12_accepted(),
    )

    assert set(material) == set(rsr.P7_R54_AHR_POST_DHR09_RSR_OP13_REQUIRED_FIELD_REFS)
    assert material["schema_version"] == rsr.P7_R54_AHR_POST_DHR09_RSR_OP13_SCHEMA_VERSION
    assert material["operation_step_ref"] == rsr.P7_R54_AHR_POST_DHR09_RSR_OP13_STEP_REF
    assert material["rsr_op13_status_ref"] == rsr.P7_R54_AHR_POST_DHR09_RSR_OP13_STATUS_MISSING_WAITING_REF
    assert material["rsr_op13_disposal_purge_receipt_missing_waiting"] is True
    assert material["rsr_op13_disposal_purge_receipt_accepted"] is False
    assert material["next_required_step"] == rsr.P7_R54_AHR_POST_DHR09_RSR_NEXT_STEP_PROVIDE_DISPOSAL_PURGE_RECEIPT_BODYFREE_REF
    assert rsr.assert_p7_r54_ahr_post_dhr09_rsr_op13_disposal_purge_receipt_intake_contract(material) is True
    _assert_common_bodyfree_no_touch_no_promotion(material)
    _assert_op13_no_purge_execution_or_completion(material)


def test_rsr_op13_accepts_bodyfree_disposal_purge_receipt_without_executing_purge_or_completing_evidence() -> None:
    op12 = _rsr_op12_accepted()
    material = rsr.build_p7_r54_ahr_post_dhr09_rsr_op13_disposal_purge_receipt_intake(
        question_need_observation_rows_intake=op12,
        disposal_purge_receipt=_valid_disposal_purge_receipt(op12),
    )

    assert material["rsr_op13_status_ref"] == rsr.P7_R54_AHR_POST_DHR09_RSR_OP13_STATUS_ACCEPTED_BODYFREE_REF
    assert material["disposal_purge_receipt_contract_valid"] is True
    assert material["disposal_purge_receipt_accepted_by_rsr_op13"] is True
    assert material["disposal_purge_receipt_accepted_without_purge_execution_by_helper"] is True
    assert material["body_full_transient_material_reported_purged"] is True
    assert material["local_temp_material_reported_purged"] is True
    assert material["reviewer_working_form_body_reported_purged"] is True
    assert material["final_no_leak_source_kind_validation_required_next"] is True
    assert material["actual_review_evidence_complete_here"] is False
    assert material["next_required_step"] == rsr.P7_R54_AHR_POST_DHR09_RSR_OP14_STEP_REF
    assert rsr.assert_p7_r54_ahr_post_dhr09_rsr_op13_disposal_purge_receipt_intake_contract(material) is True
    _assert_common_bodyfree_no_touch_no_promotion(material)
    _assert_op13_no_purge_execution_or_completion(material)


@pytest.mark.parametrize(
    ("mutator", "expected_blocker"),
    [
        (lambda receipt: receipt.__setitem__("body_full_packet_retained", True), "disposal_purge_receipt_body_full_packet_retained_not_false"),
        (lambda receipt: receipt.__setitem__("local_temp_material_retained", True), "disposal_purge_receipt_local_temp_material_retained_not_false"),
        (lambda receipt: receipt.__setitem__("external_export_performed", True), "disposal_purge_receipt_external_export_performed_not_false"),
        (lambda receipt: receipt.__setitem__("local_path_included", True), "disposal_purge_receipt_local_path_included_not_false"),
        (lambda receipt: receipt.__setitem__("terminal_output_body_included", True), "disposal_purge_receipt_terminal_output_body_included_not_false"),
        (lambda receipt: receipt.__setitem__("question_text", "do not leak purge question text"), "disposal_purge_receipt_forbidden_payload_key_detected"),
    ],
)
def test_rsr_op13_blocks_purge_receipts_with_retention_export_body_or_terminal_leak(mutator, expected_blocker: str) -> None:
    op12 = _rsr_op12_accepted()
    receipt = _valid_disposal_purge_receipt(op12)
    mutator(receipt)
    material = rsr.build_p7_r54_ahr_post_dhr09_rsr_op13_disposal_purge_receipt_intake(
        question_need_observation_rows_intake=op12,
        disposal_purge_receipt=receipt,
    )

    assert material["rsr_op13_status_ref"] == rsr.P7_R54_AHR_POST_DHR09_RSR_OP13_STATUS_BODY_LEAK_OR_RETENTION_BLOCKED_REF
    assert material["rsr_op13_disposal_purge_receipt_accepted"] is False
    assert expected_blocker in material["op13_blocker_refs"]
    assert material["actual_review_evidence_complete_here"] is False
    assert "do not leak purge question text" not in repr(material)
    assert rsr.assert_p7_r54_ahr_post_dhr09_rsr_op13_disposal_purge_receipt_intake_contract(material) is True
    _assert_common_bodyfree_no_touch_no_promotion(material)
    _assert_op13_no_purge_execution_or_completion(material)


def test_rsr_op13_repairs_invalid_purge_receipt_mismatch_without_completion_claim() -> None:
    op12 = _rsr_op12_accepted()
    receipt = _valid_disposal_purge_receipt(op12)
    receipt["packet_request_ref"] = "different_packet_request_ref"
    material = rsr.build_p7_r54_ahr_post_dhr09_rsr_op13_disposal_purge_receipt_intake(
        question_need_observation_rows_intake=op12,
        disposal_purge_receipt=receipt,
    )

    assert material["rsr_op13_status_ref"] == rsr.P7_R54_AHR_POST_DHR09_RSR_OP13_STATUS_INVALID_REPAIR_REQUIRED_REF
    assert "disposal_purge_receipt_packet_request_ref_mismatch" in material["op13_blocker_refs"]
    assert material["rsr_op13_disposal_purge_receipt_accepted"] is False
    assert material["actual_review_evidence_complete_here"] is False
    assert rsr.assert_p7_r54_ahr_post_dhr09_rsr_op13_disposal_purge_receipt_intake_contract(material) is True
    _assert_common_bodyfree_no_touch_no_promotion(material)
    _assert_op13_no_purge_execution_or_completion(material)


@pytest.mark.parametrize(
    ("field", "bad_value"),
    [
        ("disposal_purge_receipt_accepted_by_rsr_op13", False),
        ("disposal_purge_receipt_accepted_without_purge_execution_by_helper", False),
        ("helper_executes_disposal_purge", True),
        ("actual_disposal_purge_executed_here_by_helper", True),
        ("actual_disposal_purge_executed_here", True),
        ("actual_review_evidence_complete_here", True),
        ("rsr_op13_does_not_execute_disposal_purge", False),
        ("rsr_op13_does_not_complete_actual_evidence", False),
        ("dmd_execution_started_here", True),
        ("r52_actual_execution_started_here", True),
        ("p8_start_allowed", True),
        ("p7_complete", True),
        ("release_allowed", True),
        ("next_required_step", rsr.P7_R54_AHR_POST_DHR09_RSR_OP15_STEP_REF),
    ],
)
def test_rsr_op13_contract_rejects_purge_execution_completion_or_downstream_promotion_mutations(field: str, bad_value: object) -> None:
    op12 = _rsr_op12_accepted()
    material = rsr.build_p7_r54_ahr_post_dhr09_rsr_op13_disposal_purge_receipt_intake(
        question_need_observation_rows_intake=op12,
        disposal_purge_receipt=_valid_disposal_purge_receipt(op12),
    )
    material[field] = bad_value

    with pytest.raises(ValueError):
        rsr.assert_p7_r54_ahr_post_dhr09_rsr_op13_disposal_purge_receipt_intake_contract(material)


def test_rsr_op12_op13_full_title_aliases_match_canonical_builders() -> None:
    op11 = _rsr_op11_accepted()
    rows = _valid_question_need_observation_rows(op11)
    canonical_op12 = rsr.build_p7_r54_ahr_post_dhr09_rsr_op12_question_need_observation_rows_intake_p7_p8_bridge_material_only(
        review_rows_rating_rows_intake=op11,
        question_need_observation_rows=rows,
    )
    alias_op12 = rsr.build_p7_r54_ahr_post_dhr09_actual_local_review_retry_start_decision_rsr_op12_question_need_observation_rows_intake_p7_p8_bridge_material_only(
        review_rows_rating_rows_intake=op11,
        question_need_observation_rows=rows,
    )
    assert alias_op12 == canonical_op12
    assert rsr.assert_p7_r54_ahr_post_dhr09_actual_local_review_retry_start_decision_rsr_op12_question_need_observation_rows_intake_p7_p8_bridge_material_only_contract(alias_op12) is True

    receipt = _valid_disposal_purge_receipt(alias_op12)
    canonical_op13 = rsr.build_p7_r54_ahr_post_dhr09_rsr_op13_disposal_purge_receipt_intake(
        question_need_observation_rows_intake=alias_op12,
        disposal_purge_receipt=receipt,
    )
    alias_op13 = rsr.build_p7_r54_ahr_post_dhr09_actual_local_review_retry_start_decision_rsr_op13_disposal_purge_receipt_intake(
        question_need_observation_rows_intake=alias_op12,
        disposal_purge_receipt=receipt,
    )
    assert alias_op13 == canonical_op13
    assert rsr.assert_p7_r54_ahr_post_dhr09_actual_local_review_retry_start_decision_rsr_op13_disposal_purge_receipt_intake_contract(alias_op13) is True
