# -*- coding: utf-8 -*-
"""R54-AHR Post-RSR16 DRI-OP06/OP07 question-need and purge receipt revalidation tests."""

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
from test_r54_ahr_post_dhr09_actual_local_review_retry_start_decision_rsr_op12_op13_20260704 import (
    _rsr_op12_accepted,
    _valid_disposal_purge_receipt,
    _valid_question_need_observation_rows,
)
from test_r54_ahr_post_rsr16_dhr_actual_source_claim_reintake_dri_op04_op05_20260705 import (
    _assert_common_bodyfree_no_touch_no_promotion,
    _op05_ready,
)


def _op12_accepted() -> dict[str, object]:
    return _rsr_op12_accepted()


def _op06_ready(
    op05: dict[str, object] | None = None,
    op12: dict[str, object] | None = None,
) -> dict[str, object]:
    material = dri.build_p7_r54_ahr_post_rsr16_dri_op06_question_need_rows_bridge_only_revalidation(
        dri_op05_sanitized_rows_rating_rows_revalidation=op05 or _op05_ready(),
        rsr_op12_question_need_observation_rows_intake=op12 or _op12_accepted(),
    )
    assert dri.assert_p7_r54_ahr_post_rsr16_dri_op06_question_need_rows_bridge_only_revalidation_contract(material) is True
    return material


def _op13_accepted(op12: dict[str, object] | None = None) -> dict[str, object]:
    selected_op12 = op12 or _op12_accepted()
    material = rsr.build_p7_r54_ahr_post_dhr09_rsr_op13_disposal_purge_receipt_intake(
        question_need_observation_rows_intake=selected_op12,
        disposal_purge_receipt=_valid_disposal_purge_receipt(selected_op12),
    )
    assert rsr.assert_p7_r54_ahr_post_dhr09_rsr_op13_disposal_purge_receipt_intake_contract(material) is True
    assert material["rsr_op13_disposal_purge_receipt_accepted"] is True
    return material


def _op07_ready(
    op06: dict[str, object] | None = None,
    op13: dict[str, object] | None = None,
) -> dict[str, object]:
    if op06 is None and op13 is None:
        op12 = _op12_accepted()
        op06 = _op06_ready(op12=op12)
        op13 = _op13_accepted(op12=op12)
    material = dri.build_p7_r54_ahr_post_rsr16_dri_op07_disposal_purge_receipt_revalidation(
        dri_op06_question_need_rows_bridge_only_revalidation=op06 or _op06_ready(),
        rsr_op13_disposal_purge_receipt_intake=op13 or _op13_accepted(),
    )
    assert dri.assert_p7_r54_ahr_post_rsr16_dri_op07_disposal_purge_receipt_revalidation_contract(material) is True
    return material


def test_dri_op06_revalidates_question_need_rows_as_p7_p8_bridge_only_without_question_or_downstream() -> None:
    material = _op06_ready()

    assert set(material) == set(dri.P7_R54_AHR_POST_RSR16_DRI_OP06_REQUIRED_FIELD_REFS)
    assert material["schema_version"] == dri.P7_R54_AHR_POST_RSR16_DRI_OP06_SCHEMA_VERSION
    assert material["operation_step_ref"] == dri.P7_R54_AHR_POST_RSR16_DRI_OP06_STEP_REF
    assert material["op05_contract_valid"] is True
    assert material["op05_rows_and_ratings_revalidated_bodyfree"] is True
    assert material["op05_ready_for_question_need_rows_bridge_only_revalidation"] is True
    assert material["rsr_op12_contract_valid"] is True
    assert material["rsr_op12_status_ref"] == rsr.P7_R54_AHR_POST_DHR09_RSR_OP12_STATUS_ACCEPTED_BODYFREE_REF
    assert material["rsr_op12_question_need_observation_rows_accepted"] is True
    assert material["question_need_observation_rows_accepted_by_rsr_op12"] is True
    assert material["actual_question_need_observation_rows_intaken_bodyfree"] is True
    assert material["question_need_observation_row_count"] == rsr.P7_R54_AHR_POST_DHR09_RSR_EXPECTED_CASE_COUNT
    assert material["question_need_observation_row_count_is_24"] is True
    assert material["question_need_rows_match_op11_case_refs"] is True
    assert material["question_need_observation_rows_bodyfree_only"] is True
    assert material["question_need_observation_rows_from_review_rows_and_rating_rows"] is True
    assert material["question_need_observation_rows_have_actual_person_source"] is True
    assert material["question_need_observation_rows_material_only"] is True
    assert material["question_need_observation_rows_have_no_question_text_or_p8_spec"] is True
    assert material["p7_p8_bridge_material_only"] is True
    assert material["p8_design_material_candidate_only"] is True
    assert material["question_observation_material_only"] is True
    assert material["question_text_materialized"] is False
    assert material["draft_question_text_materialized"] is False
    assert material["p8_question_spec_created"] is False
    assert material["p8_question_design_started_here"] is False
    assert material["question_need_rows_forbidden_payload_key_path_refs"] == []
    assert material["question_need_rows_body_like_value_path_refs"] == []
    assert material["question_need_rows_promotion_claim_refs"] == []
    assert "question_need_observation_rows" not in material
    assert material["dri_op06_status_ref"] == dri.P7_R54_AHR_POST_RSR16_DRI_OP06_STATUS_REVALIDATED_BRIDGE_ONLY_REF
    assert material["question_need_rows_bridge_only_revalidation_status_ref"] == material["dri_op06_status_ref"]
    assert material["dri_op06_question_need_rows_revalidated_bridge_only"] is True
    assert material["dri_op06_ready_for_disposal_purge_receipt_revalidation"] is True
    assert material["dri_op06_blocker_refs"] == []
    assert material["dri_op06_does_not_create_question_need_rows"] is True
    assert material["dri_op06_does_not_materialize_question_text_or_p8_spec"] is True
    assert material["dri_op06_does_not_execute_disposal_purge"] is True
    assert material["dhr_op04_adapter_candidate_materialized_by_dri_op06"] is False
    assert material["dhr_op04_called_by_dri_op06"] is False
    assert material["dhr_actual_source_claim_reintake_executed_by_dri_op06"] is False
    assert material["actual_question_need_observation_rows_materialized_here"] is False
    assert material["actual_review_evidence_complete_here"] is False
    assert material["p8_question_design_started"] is False
    assert material["release_allowed"] is False
    assert material["next_required_step"] == dri.P7_R54_AHR_POST_RSR16_DRI_OP07_STEP_REF
    _assert_common_bodyfree_no_touch_no_promotion(material)


def test_dri_op06_waits_for_missing_question_need_rows_after_op05_ready() -> None:
    material = dri.build_p7_r54_ahr_post_rsr16_dri_op06_question_need_rows_bridge_only_revalidation(
        dri_op05_sanitized_rows_rating_rows_revalidation=_op05_ready(),
    )

    assert material["rsr_op12_question_need_observation_rows_intake_present"] is False
    assert material["dri_op06_status_ref"] == dri.P7_R54_AHR_POST_RSR16_DRI_OP06_STATUS_WAIT_FOR_QUESTION_NEED_ROWS_REF
    assert material["dri_op06_wait_for_question_need_rows"] is True
    assert material["dri_op06_ready_for_disposal_purge_receipt_revalidation"] is False
    assert material["next_required_step"] == dri.P7_R54_AHR_POST_RSR16_DRI_NEXT_STEP_WAIT_FOR_QUESTION_NEED_ROWS_REF
    assert material["dhr_op04_called_here"] is False
    assert material["release_allowed"] is False
    assert dri.assert_p7_r54_ahr_post_rsr16_dri_op06_question_need_rows_bridge_only_revalidation_contract(material) is True
    _assert_common_bodyfree_no_touch_no_promotion(material)


def test_dri_op06_waits_when_op05_rows_and_ratings_are_not_ready() -> None:
    op05 = deepcopy(_op05_ready())
    op05["dri_op05_ready_for_question_need_rows_bridge_only_revalidation"] = False
    material = dri.build_p7_r54_ahr_post_rsr16_dri_op06_question_need_rows_bridge_only_revalidation(
        dri_op05_sanitized_rows_rating_rows_revalidation=op05,
        rsr_op12_question_need_observation_rows_intake=_op12_accepted(),
    )

    assert material["op05_contract_valid"] is True
    assert material["op05_ready_for_question_need_rows_bridge_only_revalidation"] is False
    assert material["dri_op06_status_ref"] == dri.P7_R54_AHR_POST_RSR16_DRI_OP06_STATUS_WAIT_FOR_QUESTION_NEED_ROWS_REF
    assert "dri_op05_rows_and_ratings_not_ready" in material["dri_op06_blocker_refs"]
    assert material["dhr_actual_source_claim_reintake_executed_here"] is False
    assert dri.assert_p7_r54_ahr_post_rsr16_dri_op06_question_need_rows_bridge_only_revalidation_contract(material) is True
    _assert_common_bodyfree_no_touch_no_promotion(material)


def test_dri_op06_repairs_invalid_question_need_row_count_without_p8_or_release_promotion() -> None:
    op12 = deepcopy(_op12_accepted())
    op12["question_need_observation_row_count"] = 23
    material = dri.build_p7_r54_ahr_post_rsr16_dri_op06_question_need_rows_bridge_only_revalidation(
        dri_op05_sanitized_rows_rating_rows_revalidation=_op05_ready(),
        rsr_op12_question_need_observation_rows_intake=op12,
    )

    assert material["rsr_op12_contract_valid"] is False
    assert material["dri_op06_status_ref"] == dri.P7_R54_AHR_POST_RSR16_DRI_OP06_STATUS_REPAIR_QUESTION_NEED_ROWS_REF
    assert "rsr_op12_contract_or_status_invalid" in material["dri_op06_blocker_refs"]
    assert material["question_text_materialized"] is False
    assert material["p8_question_spec_created"] is False
    assert material["release_allowed"] is False
    assert dri.assert_p7_r54_ahr_post_rsr16_dri_op06_question_need_rows_bridge_only_revalidation_contract(material) is True
    _assert_common_bodyfree_no_touch_no_promotion(material)


@pytest.mark.parametrize(
    ("mutator", "expected_blocker", "leaked_value"),
    [
        (lambda op12: op12.__setitem__("question_text", "do not leak DRI OP06 question text"), "dri_op06_forbidden_payload_key_detected", "do not leak DRI OP06 question text"),
        (lambda op12: op12.__setitem__("p8_question_spec_created", True), "dri_op06_promotion_claim_detected", None),
        (lambda op12: op12.__setitem__("question_need_observation_rows_have_actual_person_source", False), "question_need_rows_source_kind_not_actual_local_only_human_review_by_person", None),
    ],
)
def test_dri_op06_blocks_question_text_p8_materialization_or_invalid_source_claim(mutator, expected_blocker: str, leaked_value: str | None) -> None:
    op12 = deepcopy(_op12_accepted())
    mutator(op12)
    material = dri.build_p7_r54_ahr_post_rsr16_dri_op06_question_need_rows_bridge_only_revalidation(
        dri_op05_sanitized_rows_rating_rows_revalidation=_op05_ready(),
        rsr_op12_question_need_observation_rows_intake=op12,
    )

    assert material["dri_op06_status_ref"] == dri.P7_R54_AHR_POST_RSR16_DRI_OP06_STATUS_BLOCKED_QUESTION_TEXT_OR_P8_MATERIALIZATION_REF
    assert expected_blocker in material["dri_op06_blocker_refs"]
    assert material["dri_op06_question_text_or_p8_materialization_blocked"] is True
    assert material["dri_op06_ready_for_disposal_purge_receipt_revalidation"] is False
    assert material["dhr_op04_called_here"] is False
    assert material["p8_question_design_started"] is False
    if leaked_value is not None:
        assert leaked_value not in repr(material)
    assert dri.assert_p7_r54_ahr_post_rsr16_dri_op06_question_need_rows_bridge_only_revalidation_contract(material) is True
    _assert_common_bodyfree_no_touch_no_promotion(material)


@pytest.mark.parametrize(
    ("field", "bad_value"),
    [
        ("schema_version", "wrong.schema"),
        ("dri_op06_status_ref", dri.P7_R54_AHR_POST_RSR16_DRI_OP06_STATUS_WAIT_FOR_QUESTION_NEED_ROWS_REF),
        ("next_required_step", dri.P7_R54_AHR_POST_RSR16_DRI_OP08_STEP_REF),
        ("dhr_op04_called_by_dri_op06", True),
        ("dhr_actual_source_claim_reintake_executed_by_dri_op06", True),
        ("question_text_materialized", True),
        ("p8_question_spec_created", True),
        ("p8_question_design_started", True),
        ("release_allowed", True),
        ("body_free", False),
    ],
)
def test_dri_op06_contract_rejects_question_text_downstream_or_boundary_mutations(field: str, bad_value: object) -> None:
    material = _op06_ready()
    material[field] = bad_value

    with pytest.raises(ValueError):
        dri.assert_p7_r54_ahr_post_rsr16_dri_op06_question_need_rows_bridge_only_revalidation_contract(material)


def test_dri_op07_revalidates_bodyfree_purge_receipt_without_executing_purge_or_completing_evidence() -> None:
    material = _op07_ready()

    assert set(material) == set(dri.P7_R54_AHR_POST_RSR16_DRI_OP07_REQUIRED_FIELD_REFS)
    assert material["schema_version"] == dri.P7_R54_AHR_POST_RSR16_DRI_OP07_SCHEMA_VERSION
    assert material["operation_step_ref"] == dri.P7_R54_AHR_POST_RSR16_DRI_OP07_STEP_REF
    assert material["op06_contract_valid"] is True
    assert material["op06_question_need_rows_revalidated_bridge_only"] is True
    assert material["op06_ready_for_disposal_purge_receipt_revalidation"] is True
    assert material["rsr_op13_contract_valid"] is True
    assert material["rsr_op13_status_ref"] == rsr.P7_R54_AHR_POST_DHR09_RSR_OP13_STATUS_ACCEPTED_BODYFREE_REF
    assert material["rsr_op13_disposal_purge_receipt_accepted"] is True
    assert material["disposal_purge_receipt_accepted_by_rsr_op13"] is True
    assert material["disposal_purge_receipt_accepted_without_purge_execution_by_helper"] is True
    assert material["final_no_leak_source_kind_validation_required_next"] is True
    assert material["operation_receipt_ref_matches_op06"] is True
    assert material["review_session_id_matches_op06"] is True
    assert material["disposal_purge_receipt_source_kind_is_actual_local_only_human_review_by_person"] is True
    assert material["disposal_purge_receipt_purge_completed"] is True
    assert material["disposal_purge_receipt_body_free"] is True
    assert material["body_full_transient_material_reported_purged"] is True
    assert material["local_temp_material_reported_purged"] is True
    assert material["reviewer_working_form_body_reported_purged"] is True
    assert material["disposal_purge_receipt_body_full_packet_retained"] is False
    assert material["disposal_purge_receipt_local_temp_material_retained"] is False
    assert material["disposal_purge_receipt_external_export_performed"] is False
    assert material["disposal_purge_receipt_forbidden_payload_key_path_refs"] == []
    assert material["disposal_purge_receipt_body_like_value_path_refs"] == []
    assert material["disposal_purge_receipt_promotion_claim_refs"] == []
    assert material["disposal_purge_receipt_retention_or_export_blocker_refs"] == []
    assert material["dri_op07_status_ref"] == dri.P7_R54_AHR_POST_RSR16_DRI_OP07_STATUS_REVALIDATED_BODYFREE_REF
    assert material["disposal_purge_receipt_revalidation_status_ref"] == material["dri_op07_status_ref"]
    assert material["dri_op07_disposal_purge_receipt_revalidated_bodyfree"] is True
    assert material["dri_op07_ready_for_final_bodyfree_no_promotion_source_kind_rescan"] is True
    assert material["dri_op07_blocker_refs"] == []
    assert material["dri_op07_does_not_execute_disposal_purge"] is True
    assert material["dri_op07_does_not_complete_actual_evidence"] is True
    assert material["dri_op07_does_not_materialize_p8_question_spec"] is True
    assert material["disposal_purge_executed_by_dri_op07"] is False
    assert material["actual_disposal_purge_executed_here"] is False
    assert material["actual_review_evidence_complete_here"] is False
    assert material["dhr_op04_called_here"] is False
    assert material["p8_question_design_started"] is False
    assert material["release_allowed"] is False
    assert material["next_required_step"] == dri.P7_R54_AHR_POST_RSR16_DRI_OP08_STEP_REF
    _assert_common_bodyfree_no_touch_no_promotion(material)


def test_dri_op07_waits_for_missing_disposal_purge_receipt_after_op06_ready() -> None:
    material = dri.build_p7_r54_ahr_post_rsr16_dri_op07_disposal_purge_receipt_revalidation(
        dri_op06_question_need_rows_bridge_only_revalidation=_op06_ready(),
    )

    assert material["rsr_op13_disposal_purge_receipt_intake_present"] is False
    assert material["dri_op07_status_ref"] == dri.P7_R54_AHR_POST_RSR16_DRI_OP07_STATUS_WAIT_FOR_PURGE_RECEIPT_REF
    assert material["dri_op07_wait_for_disposal_purge_receipt"] is True
    assert material["dri_op07_ready_for_final_bodyfree_no_promotion_source_kind_rescan"] is False
    assert material["next_required_step"] == dri.P7_R54_AHR_POST_RSR16_DRI_NEXT_STEP_WAIT_FOR_PURGE_RECEIPT_REF
    assert material["actual_disposal_purge_executed_here"] is False
    assert material["release_allowed"] is False
    assert dri.assert_p7_r54_ahr_post_rsr16_dri_op07_disposal_purge_receipt_revalidation_contract(material) is True
    _assert_common_bodyfree_no_touch_no_promotion(material)


def test_dri_op07_waits_when_op06_question_need_rows_are_not_ready() -> None:
    op06 = dri.build_p7_r54_ahr_post_rsr16_dri_op06_question_need_rows_bridge_only_revalidation(
        dri_op05_sanitized_rows_rating_rows_revalidation=_op05_ready(),
    )
    assert dri.assert_p7_r54_ahr_post_rsr16_dri_op06_question_need_rows_bridge_only_revalidation_contract(op06) is True
    material = dri.build_p7_r54_ahr_post_rsr16_dri_op07_disposal_purge_receipt_revalidation(
        dri_op06_question_need_rows_bridge_only_revalidation=op06,
        rsr_op13_disposal_purge_receipt_intake=_op13_accepted(),
    )

    assert material["op06_question_need_rows_revalidated_bridge_only"] is False
    assert material["op06_ready_for_disposal_purge_receipt_revalidation"] is False
    assert material["dri_op07_status_ref"] == dri.P7_R54_AHR_POST_RSR16_DRI_OP07_STATUS_WAIT_FOR_PURGE_RECEIPT_REF
    assert "dri_op06_question_need_rows_not_ready" in material["dri_op07_blocker_refs"]
    assert material["dhr_actual_source_claim_reintake_executed_here"] is False
    assert dri.assert_p7_r54_ahr_post_rsr16_dri_op07_disposal_purge_receipt_revalidation_contract(material) is True
    _assert_common_bodyfree_no_touch_no_promotion(material)


def test_dri_op07_repairs_invalid_disposal_purge_receipt_contract_without_completion_claim() -> None:
    op12 = _op12_accepted()
    op13 = _op13_accepted(op12)
    op13["schema_version"] = "wrong.schema"
    material = dri.build_p7_r54_ahr_post_rsr16_dri_op07_disposal_purge_receipt_revalidation(
        dri_op06_question_need_rows_bridge_only_revalidation=_op06_ready(op12=op12),
        rsr_op13_disposal_purge_receipt_intake=op13,
    )

    assert material["rsr_op13_contract_valid"] is False
    assert material["rsr_op13_status_ref"] == rsr.P7_R54_AHR_POST_DHR09_RSR_OP13_STATUS_ACCEPTED_BODYFREE_REF
    assert material["dri_op07_status_ref"] == dri.P7_R54_AHR_POST_RSR16_DRI_OP07_STATUS_REPAIR_PURGE_RECEIPT_REF
    assert "rsr_op13_contract_or_status_invalid" in material["dri_op07_blocker_refs"]
    assert material["actual_review_evidence_complete_here"] is False
    assert material["release_allowed"] is False
    assert dri.assert_p7_r54_ahr_post_rsr16_dri_op07_disposal_purge_receipt_revalidation_contract(material) is True
    _assert_common_bodyfree_no_touch_no_promotion(material)


@pytest.mark.parametrize(
    ("mutator", "expected_blocker", "leaked_value"),
    [
        (lambda op13: op13.__setitem__("disposal_purge_receipt_body_full_packet_retained", True), "disposal_purge_receipt_retention_or_export_flag_true", None),
        (lambda op13: op13.__setitem__("local_path", "/tmp/dri_op07_should_not_leak"), "dri_op07_forbidden_payload_key_detected", "/tmp/dri_op07_should_not_leak"),
        (lambda op13: op13.__setitem__("actual_disposal_purge_executed_here", True), "dri_op07_promotion_claim_detected", None),
    ],
)
def test_dri_op07_blocks_retention_path_leak_or_helper_purge_execution_claim(mutator, expected_blocker: str, leaked_value: str | None) -> None:
    op12 = _op12_accepted()
    op13 = _op13_accepted(op12)
    mutator(op13)
    material = dri.build_p7_r54_ahr_post_rsr16_dri_op07_disposal_purge_receipt_revalidation(
        dri_op06_question_need_rows_bridge_only_revalidation=_op06_ready(op12=op12),
        rsr_op13_disposal_purge_receipt_intake=op13,
    )

    assert material["dri_op07_status_ref"] == dri.P7_R54_AHR_POST_RSR16_DRI_OP07_STATUS_BLOCKED_PURGE_RECEIPT_BODY_LEAK_OR_RETENTION_REF
    assert expected_blocker in material["dri_op07_blocker_refs"]
    assert material["dri_op07_purge_receipt_body_leak_or_retention_blocked"] is True
    assert material["dri_op07_ready_for_final_bodyfree_no_promotion_source_kind_rescan"] is False
    assert material["actual_disposal_purge_executed_here"] is False
    assert material["dhr_op04_called_here"] is False
    assert material["release_allowed"] is False
    if leaked_value is not None:
        assert leaked_value not in repr(material)
    assert dri.assert_p7_r54_ahr_post_rsr16_dri_op07_disposal_purge_receipt_revalidation_contract(material) is True
    _assert_common_bodyfree_no_touch_no_promotion(material)


@pytest.mark.parametrize(
    ("field", "bad_value"),
    [
        ("schema_version", "wrong.schema"),
        ("dri_op07_status_ref", dri.P7_R54_AHR_POST_RSR16_DRI_OP07_STATUS_WAIT_FOR_PURGE_RECEIPT_REF),
        ("next_required_step", dri.P7_R54_AHR_POST_RSR16_DRI_OP09_STEP_REF),
        ("helper_executes_disposal_purge", True),
        ("actual_disposal_purge_executed_here_by_helper", True),
        ("disposal_purge_executed_by_dri_op07", True),
        ("dhr_op04_called_by_dri_op07", True),
        ("dhr_actual_source_claim_reintake_executed_by_dri_op07", True),
        ("actual_review_evidence_complete_here", True),
        ("p8_question_design_started", True),
        ("release_allowed", True),
        ("body_free", False),
    ],
)
def test_dri_op07_contract_rejects_purge_execution_downstream_or_boundary_mutations(field: str, bad_value: object) -> None:
    material = _op07_ready()
    material[field] = bad_value

    with pytest.raises(ValueError):
        dri.assert_p7_r54_ahr_post_rsr16_dri_op07_disposal_purge_receipt_revalidation_contract(material)


def test_dri_op06_op07_full_title_aliases_match_canonical_builders() -> None:
    op12 = _op12_accepted()
    op05 = _op05_ready()
    canonical_op06 = dri.build_p7_r54_ahr_post_rsr16_dri_op06_question_need_rows_bridge_only_revalidation(
        dri_op05_sanitized_rows_rating_rows_revalidation=op05,
        rsr_op12_question_need_observation_rows_intake=op12,
    )
    alias_op06 = dri.build_p7_r54_ahr_post_rsr16_dhr_actual_source_claim_reintake_dri_op06_question_need_rows_bridge_only_revalidation(
        dri_op05_sanitized_rows_rating_rows_revalidation=op05,
        rsr_op12_question_need_observation_rows_intake=op12,
    )
    assert alias_op06 == canonical_op06
    assert dri.assert_p7_r54_ahr_post_rsr16_dhr_actual_source_claim_reintake_dri_op06_question_need_rows_bridge_only_revalidation_contract(alias_op06) is True

    op13 = _op13_accepted(op12)
    canonical_op07 = dri.build_p7_r54_ahr_post_rsr16_dri_op07_disposal_purge_receipt_revalidation(
        dri_op06_question_need_rows_bridge_only_revalidation=alias_op06,
        rsr_op13_disposal_purge_receipt_intake=op13,
    )
    alias_op07 = dri.build_p7_r54_ahr_post_rsr16_dhr_actual_source_claim_reintake_dri_op07_disposal_purge_receipt_revalidation(
        dri_op06_question_need_rows_bridge_only_revalidation=alias_op06,
        rsr_op13_disposal_purge_receipt_intake=op13,
    )
    assert alias_op07 == canonical_op07
    assert dri.assert_p7_r54_ahr_post_rsr16_dhr_actual_source_claim_reintake_dri_op07_disposal_purge_receipt_revalidation_contract(alias_op07) is True
