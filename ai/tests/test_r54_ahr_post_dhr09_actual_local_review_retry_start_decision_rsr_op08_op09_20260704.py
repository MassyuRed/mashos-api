# -*- coding: utf-8 -*-
"""R54-AHR Post-DHR09 RSR-OP08/OP09 selection-form/lifecycle-boundary tests."""

from __future__ import annotations

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
from test_r54_ahr_post_dhr09_actual_local_review_retry_start_decision_rsr_op06_op07_20260704 import (
    _rsr_op06_ready,
    _valid_packet_generation_receipt,
)


def _rsr_op07_ready() -> dict[str, object]:
    op06 = _rsr_op06_ready()
    material = rsr.build_p7_r54_ahr_post_dhr09_rsr_op07_body_full_packet_generation_receipt_export_denylist_scan_intake(
        body_full_packet_transient_request_boundary=op06,
        body_full_packet_generation_receipt=_valid_packet_generation_receipt(op06),
    )
    assert rsr.assert_p7_r54_ahr_post_dhr09_rsr_op07_body_full_packet_generation_receipt_export_denylist_scan_intake_contract(material) is True
    assert material["rsr_op07_ready_for_selection_only_reviewer_form_rating_axis_contract_freeze"] is True
    return material


def _rsr_op08_ready() -> dict[str, object]:
    material = rsr.build_p7_r54_ahr_post_dhr09_rsr_op08_selection_only_reviewer_form_rating_axis_contract_freeze(
        packet_generation_receipt_intake=_rsr_op07_ready(),
    )
    assert rsr.assert_p7_r54_ahr_post_dhr09_rsr_op08_selection_only_reviewer_form_rating_axis_contract_freeze_contract(material) is True
    assert material["rsr_op08_ready_for_actual_local_only_review_lifecycle_state_capture"] is True
    return material


def _assert_op08_no_actual_or_p8(material: dict[str, object]) -> None:
    assert material["rsr_op08_does_not_run_actual_local_human_review"] is True
    assert material["rsr_op08_does_not_create_actual_operation_receipt_rows_or_disposal"] is True
    assert material["rsr_op08_does_not_materialize_question_text_or_p8_spec"] is True
    assert material["question_text_materialized"] is False
    assert material["draft_question_text_materialized"] is False
    assert material["p8_question_spec_created"] is False
    assert material["p8_question_design_started_here"] is False
    assert material["actual_local_human_review_executed_here"] is False
    assert material["actual_operation_receipt_created_here"] is False
    assert material["actual_rows_created_here"] is False
    assert material["actual_question_need_observation_rows_materialized_here"] is False
    assert material["p8_start_allowed"] is False
    assert material["p8_question_design_started"] is False
    assert material["release_allowed"] is False


def _assert_op09_no_actual_or_receipt(material: dict[str, object]) -> None:
    assert material["helper_executes_actual_review"] is False
    assert material["actual_local_human_review_executed_here_by_helper"] is False
    assert material["actual_operation_receipt_accepted_by_op09"] is False
    assert material["rsr_op09_does_not_generate_body_full_packet"] is True
    assert material["rsr_op09_does_not_run_actual_local_human_review"] is True
    assert material["rsr_op09_does_not_create_actual_operation_receipt_rows_or_disposal"] is True
    assert material["body_full_packet_generated_here"] is False
    assert material["actual_local_human_review_executed_here"] is False
    assert material["actual_operation_receipt_created_here"] is False
    assert material["actual_rows_created_here"] is False
    assert material["actual_disposal_purge_executed_here"] is False
    assert material["dmd_execution_started_here"] is False
    assert material["r52_actual_execution_started_here"] is False
    assert material["p8_start_allowed"] is False
    assert material["release_allowed"] is False


def test_rsr_op08_waits_when_packet_generation_receipt_intake_is_not_ready() -> None:
    material = rsr.build_p7_r54_ahr_post_dhr09_rsr_op08_selection_only_reviewer_form_rating_axis_contract_freeze()

    assert set(material) == set(rsr.P7_R54_AHR_POST_DHR09_RSR_OP08_REQUIRED_FIELD_REFS)
    assert material["schema_version"] == rsr.P7_R54_AHR_POST_DHR09_RSR_OP08_SCHEMA_VERSION
    assert material["operation_step_ref"] == rsr.P7_R54_AHR_POST_DHR09_RSR_OP08_STEP_REF
    assert material["op07_contract_valid"] is True
    assert material["op07_ready_for_selection_only_reviewer_form_rating_axis_contract_freeze"] is False
    assert material["rsr_op08_status_ref"] == rsr.P7_R54_AHR_POST_DHR09_RSR_OP08_STATUS_WAITING_FOR_PACKET_GENERATION_RECEIPT_REF
    assert material["rsr_op08_waiting_for_packet_generation_receipt"] is True
    assert material["rsr_op08_ready"] is False
    assert material["selection_only_row_conversion_contract_ready"] is False
    assert material["next_required_step"] == rsr.P7_R54_AHR_POST_DHR09_RSR_NEXT_STEP_WAIT_FOR_PACKET_GENERATION_RECEIPT_BEFORE_SELECTION_FORM_CONTRACT_REF
    _assert_op08_no_actual_or_p8(material)
    assert rsr.assert_p7_r54_ahr_post_dhr09_rsr_op08_selection_only_reviewer_form_rating_axis_contract_freeze_contract(material) is True
    _assert_common_bodyfree_no_touch_no_promotion(material)


def test_rsr_op08_accepts_selection_only_rating_axis_contract_without_review_rows_or_p8_question() -> None:
    material = _rsr_op08_ready()

    assert material["rsr_op08_status_ref"] == rsr.P7_R54_AHR_POST_DHR09_RSR_OP08_STATUS_ACCEPTED_BODYFREE_REF
    assert material["op07_packet_generation_receipt_accepted"] is True
    assert material["op07_packet_generation_receipt_accepted_but_actual_review_not_executed"] is True
    assert material["rating_axis_target_refs"] == list(rsr.P7_R54_AHR_POST_DHR09_RSR_OP08_RATING_AXIS_TARGET_REFS.keys())
    assert material["rating_axis_target_ref_count"] == 6
    assert material["rating_axis_target_threshold_ref_count"] == 6
    assert material["score_option_refs"] == list(rsr.P7_R54_AHR_POST_DHR09_RSR_OP08_SCORE_OPTION_REFS)
    assert material["score_option_ref_count"] == 5
    assert material["question_need_class_refs"] == list(rsr.P7_R54_AHR_POST_DHR09_RSR_OP08_QUESTION_NEED_CLASS_REFS)
    assert material["question_need_class_ref_count"] == 9
    assert material["selection_only_form_required"] is True
    assert material["selection_only_form_used_for_contract"] is True
    assert material["selection_only_row_conversion_contract_ready"] is True
    assert material["reviewer_free_text_allowed"] is False
    assert material["body_full_packet_body_allowed_in_form"] is False
    assert material["question_text_allowed_in_form"] is False
    assert material["rsr_op08_ready_for_actual_local_only_review_lifecycle_state_capture"] is True
    assert material["selection_only_form_contract_accepted_but_no_review_rows_created"] is True
    assert material["next_required_step"] == rsr.P7_R54_AHR_POST_DHR09_RSR_OP09_STEP_REF
    _assert_op08_no_actual_or_p8(material)
    _assert_common_bodyfree_no_touch_no_promotion(material)


@pytest.mark.parametrize(
    ("payload", "expected_status", "expected_blocker"),
    [
        ({"body_free": False}, rsr.P7_R54_AHR_POST_DHR09_RSR_OP08_STATUS_INVALID_REPAIR_REQUIRED_REF, "selection_form_contract_material_body_free_not_true"),
        ({"question_text": "do not materialize a question", "body_free": True}, rsr.P7_R54_AHR_POST_DHR09_RSR_OP08_STATUS_BODY_LEAK_BLOCKED_REF, "selection_form_forbidden_payload_key_detected"),
        ({"reviewer_free_text": "free text must not leak", "body_free": True}, rsr.P7_R54_AHR_POST_DHR09_RSR_OP08_STATUS_BODY_LEAK_BLOCKED_REF, "selection_form_forbidden_payload_key_detected"),
        ({"actual_local_human_review_executed_here": True, "body_free": True}, rsr.P7_R54_AHR_POST_DHR09_RSR_OP08_STATUS_BODY_LEAK_BLOCKED_REF, "selection_form_promotion_claim_detected"),
    ],
)
def test_rsr_op08_repairs_or_blocks_invalid_selection_form_contract_material(payload: dict[str, object], expected_status: str, expected_blocker: str) -> None:
    material = rsr.build_p7_r54_ahr_post_dhr09_rsr_op08_selection_only_reviewer_form_rating_axis_contract_freeze(
        packet_generation_receipt_intake=_rsr_op07_ready(),
        selection_form_contract_material=payload,
    )

    assert material["rsr_op08_status_ref"] == expected_status
    assert expected_blocker in material["selection_form_blocker_refs"]
    assert material["rsr_op08_ready"] is False
    assert material["selection_only_row_conversion_contract_ready"] is False
    assert material["selection_only_form_contract_accepted_but_no_review_rows_created"] is False
    assert material["next_required_step"] in (
        rsr.P7_R54_AHR_POST_DHR09_RSR_NEXT_STEP_REPAIR_SELECTION_ONLY_REVIEWER_FORM_CONTRACT_REF,
        rsr.P7_R54_AHR_POST_DHR09_RSR_NEXT_STEP_BLOCKED_SELECTION_ONLY_FORM_BODY_LEAK_BEFORE_LIFECYCLE_REF,
    )
    assert "do not materialize a question" not in repr(material)
    assert "free text must not leak" not in repr(material)
    _assert_op08_no_actual_or_p8(material)
    assert rsr.assert_p7_r54_ahr_post_dhr09_rsr_op08_selection_only_reviewer_form_rating_axis_contract_freeze_contract(material) is True
    _assert_common_bodyfree_no_touch_no_promotion(material)


@pytest.mark.parametrize(
    ("field", "bad_value"),
    [
        ("selection_only_form_required", False),
        ("selection_only_form_used_for_contract", False),
        ("rating_axis_target_refs", ["history_connection_naturalness"]),
        ("score_option_refs", [0.0, 1.0]),
        ("question_need_class_refs", ["no_question_needed_emlis_can_observe"]),
        ("question_text_materialized", True),
        ("draft_question_text_materialized", True),
        ("p8_question_spec_created", True),
        ("reviewer_free_text_allowed", True),
        ("actual_local_human_review_executed_here", True),
        ("actual_rows_created_here", True),
        ("p8_start_allowed", True),
        ("release_allowed", True),
        ("next_required_step", rsr.P7_R54_AHR_POST_DHR09_RSR_OP10_STEP_REF),
    ],
)
def test_rsr_op08_contract_rejects_question_materialization_actual_rows_or_promotion_mutations(field: str, bad_value: object) -> None:
    material = _rsr_op08_ready()
    material[field] = bad_value

    with pytest.raises(ValueError):
        rsr.assert_p7_r54_ahr_post_dhr09_rsr_op08_selection_only_reviewer_form_rating_axis_contract_freeze_contract(material)


def test_rsr_op09_waits_when_selection_form_contract_is_not_ready() -> None:
    material = rsr.build_p7_r54_ahr_post_dhr09_rsr_op09_actual_local_only_review_lifecycle_state_capture()

    assert set(material) == set(rsr.P7_R54_AHR_POST_DHR09_RSR_OP09_REQUIRED_FIELD_REFS)
    assert material["schema_version"] == rsr.P7_R54_AHR_POST_DHR09_RSR_OP09_SCHEMA_VERSION
    assert material["operation_step_ref"] == rsr.P7_R54_AHR_POST_DHR09_RSR_OP09_STEP_REF
    assert material["op08_contract_valid"] is True
    assert material["op08_ready_for_actual_local_only_review_lifecycle_state_capture"] is False
    assert material["rsr_op09_status_ref"] == rsr.P7_R54_AHR_POST_DHR09_RSR_OP09_STATUS_WAITING_FOR_SELECTION_FORM_CONTRACT_REF
    assert material["rsr_op09_waiting_for_selection_form_contract"] is True
    assert material["review_lifecycle_state_captured_bodyfree"] is False
    assert material["actual_operation_receipt_required"] is False
    assert material["next_required_step"] == rsr.P7_R54_AHR_POST_DHR09_RSR_NEXT_STEP_WAIT_FOR_SELECTION_FORM_CONTRACT_BEFORE_LIFECYCLE_CAPTURE_REF
    _assert_op09_no_actual_or_receipt(material)
    assert rsr.assert_p7_r54_ahr_post_dhr09_rsr_op09_actual_local_only_review_lifecycle_state_capture_contract(material) is True
    _assert_common_bodyfree_no_touch_no_promotion(material)


@pytest.mark.parametrize(
    ("status", "flag", "next_step"),
    [
        (rsr.P7_R54_AHR_POST_DHR09_RSR_REVIEW_LIFECYCLE_STATUS_NOT_STARTED_REF, "rsr_op09_review_operation_not_started", rsr.P7_R54_AHR_POST_DHR09_RSR_NEXT_STEP_START_OR_CONTINUE_ACTUAL_LOCAL_ONLY_REVIEW_OPERATION_LOCAL_ONLY_REF),
        (rsr.P7_R54_AHR_POST_DHR09_RSR_REVIEW_LIFECYCLE_STATUS_READY_TO_START_REF, "rsr_op09_review_operation_ready_to_start", rsr.P7_R54_AHR_POST_DHR09_RSR_NEXT_STEP_START_OR_CONTINUE_ACTUAL_LOCAL_ONLY_REVIEW_OPERATION_LOCAL_ONLY_REF),
        (rsr.P7_R54_AHR_POST_DHR09_RSR_REVIEW_LIFECYCLE_STATUS_IN_PROGRESS_LOCAL_ONLY_REF, "rsr_op09_review_operation_in_progress_local_only", rsr.P7_R54_AHR_POST_DHR09_RSR_NEXT_STEP_START_OR_CONTINUE_ACTUAL_LOCAL_ONLY_REVIEW_OPERATION_LOCAL_ONLY_REF),
        (rsr.P7_R54_AHR_POST_DHR09_RSR_REVIEW_LIFECYCLE_STATUS_PAUSED_LOCAL_ONLY_REF, "rsr_op09_review_operation_paused_local_only", rsr.P7_R54_AHR_POST_DHR09_RSR_NEXT_STEP_START_OR_CONTINUE_ACTUAL_LOCAL_ONLY_REVIEW_OPERATION_LOCAL_ONLY_REF),
        (rsr.P7_R54_AHR_POST_DHR09_RSR_REVIEW_LIFECYCLE_STATUS_COMPLETED_RECEIPT_REQUIRED_REF, "rsr_op09_review_operation_completed_receipt_required", rsr.P7_R54_AHR_POST_DHR09_RSR_OP10_STEP_REF),
        (rsr.P7_R54_AHR_POST_DHR09_RSR_REVIEW_LIFECYCLE_STATUS_ABORTED_REPAIR_REQUIRED_REF, "rsr_op09_review_operation_aborted_repair_required", rsr.P7_R54_AHR_POST_DHR09_RSR_NEXT_STEP_REPAIR_ABORTED_ACTUAL_LOCAL_ONLY_REVIEW_LIFECYCLE_REF),
    ],
)
def test_rsr_op09_captures_allowed_lifecycle_states_without_executing_review_or_accepting_receipt(status: str, flag: str, next_step: str) -> None:
    material = rsr.build_p7_r54_ahr_post_dhr09_rsr_op09_actual_local_only_review_lifecycle_state_capture(
        selection_only_reviewer_form_contract=_rsr_op08_ready(),
        lifecycle_status_ref=status,
        lifecycle_state_material={"body_free": True},
    )

    assert material["rsr_op09_status_ref"] == status
    assert material["lifecycle_status_ref"] == status
    assert material[flag] is True
    assert material["review_lifecycle_state_captured_bodyfree"] is True
    assert material["next_required_step"] == next_step
    if status == rsr.P7_R54_AHR_POST_DHR09_RSR_REVIEW_LIFECYCLE_STATUS_COMPLETED_RECEIPT_REQUIRED_REF:
        assert material["actual_review_lifecycle_completed_but_receipt_not_accepted"] is True
        assert material["actual_operation_receipt_required"] is True
        assert material["rsr_op09_ready_for_actual_operation_receipt_intake"] is True
    else:
        assert material["actual_operation_receipt_required"] is False
        assert material["actual_operation_receipt_accepted_by_op09"] is False
    _assert_op09_no_actual_or_receipt(material)
    assert rsr.assert_p7_r54_ahr_post_dhr09_rsr_op09_actual_local_only_review_lifecycle_state_capture_contract(material) is True
    _assert_common_bodyfree_no_touch_no_promotion(material)


@pytest.mark.parametrize(
    ("payload", "status", "expected_blocker"),
    [
        ({"body_free": False}, rsr.P7_R54_AHR_POST_DHR09_RSR_OP09_STATUS_INVALID_REPAIR_REQUIRED_REF, "lifecycle_state_material_body_free_not_true"),
        ({"lifecycle_status_ref": "not_allowed_lifecycle_status", "body_free": True}, rsr.P7_R54_AHR_POST_DHR09_RSR_OP09_STATUS_INVALID_REPAIR_REQUIRED_REF, "review_lifecycle_status_ref_not_allowed"),
        ({"raw_input": "body material must not leak", "body_free": True}, rsr.P7_R54_AHR_POST_DHR09_RSR_OP09_STATUS_BODY_LEAK_BLOCKED_REF, "lifecycle_state_forbidden_payload_key_detected"),
        ({"actual_operation_receipt_created_here": True, "body_free": True}, rsr.P7_R54_AHR_POST_DHR09_RSR_OP09_STATUS_BODY_LEAK_BLOCKED_REF, "lifecycle_state_promotion_claim_detected"),
    ],
)
def test_rsr_op09_repairs_or_blocks_invalid_lifecycle_state_material(payload: dict[str, object], status: str, expected_blocker: str) -> None:
    material = rsr.build_p7_r54_ahr_post_dhr09_rsr_op09_actual_local_only_review_lifecycle_state_capture(
        selection_only_reviewer_form_contract=_rsr_op08_ready(),
        lifecycle_state_material=payload,
    )

    assert material["rsr_op09_status_ref"] == status
    assert expected_blocker in material["lifecycle_state_blocker_refs"]
    assert material["rsr_op09_ready"] is False
    assert material["review_lifecycle_state_captured_bodyfree"] is False
    assert material["actual_operation_receipt_required"] is False
    assert material["next_required_step"] in (
        rsr.P7_R54_AHR_POST_DHR09_RSR_NEXT_STEP_REPAIR_REVIEW_LIFECYCLE_STATE_CAPTURE_REF,
        rsr.P7_R54_AHR_POST_DHR09_RSR_NEXT_STEP_BLOCKED_REVIEW_LIFECYCLE_BODY_LEAK_BEFORE_RECEIPT_REF,
    )
    assert "body material must not leak" not in repr(material)
    _assert_op09_no_actual_or_receipt(material)
    assert rsr.assert_p7_r54_ahr_post_dhr09_rsr_op09_actual_local_only_review_lifecycle_state_capture_contract(material) is True
    _assert_common_bodyfree_no_touch_no_promotion(material)


@pytest.mark.parametrize(
    ("field", "bad_value"),
    [
        ("helper_executes_actual_review", True),
        ("actual_local_human_review_executed_here_by_helper", True),
        ("actual_operation_receipt_accepted_by_op09", True),
        ("actual_local_human_review_executed_here", True),
        ("actual_operation_receipt_created_here", True),
        ("actual_rows_created_here", True),
        ("dmd_execution_started_here", True),
        ("r52_actual_execution_started_here", True),
        ("p8_start_allowed", True),
        ("release_allowed", True),
        ("next_required_step", rsr.P7_R54_AHR_POST_DHR09_RSR_OP11_STEP_REF),
    ],
)
def test_rsr_op09_contract_rejects_helper_execution_receipt_acceptance_or_promotion_mutations(field: str, bad_value: object) -> None:
    material = rsr.build_p7_r54_ahr_post_dhr09_rsr_op09_actual_local_only_review_lifecycle_state_capture(
        selection_only_reviewer_form_contract=_rsr_op08_ready(),
        lifecycle_status_ref=rsr.P7_R54_AHR_POST_DHR09_RSR_REVIEW_LIFECYCLE_STATUS_COMPLETED_RECEIPT_REQUIRED_REF,
    )
    material[field] = bad_value

    with pytest.raises(ValueError):
        rsr.assert_p7_r54_ahr_post_dhr09_rsr_op09_actual_local_only_review_lifecycle_state_capture_contract(material)


def test_rsr_op08_op09_full_title_aliases_match_canonical_builders() -> None:
    op07 = _rsr_op07_ready()
    op08_alias = rsr.build_p7_r54_ahr_post_dhr09_actual_local_review_retry_start_decision_rsr_op08_selection_only_reviewer_form_rating_axis_contract_freeze(
        packet_generation_receipt_intake=op07,
    )
    op08_canonical = rsr.build_p7_r54_ahr_post_dhr09_rsr_op08_selection_only_reviewer_form_rating_axis_contract_freeze(
        packet_generation_receipt_intake=op07,
    )
    assert op08_alias == op08_canonical
    assert rsr.assert_p7_r54_ahr_post_dhr09_actual_local_review_retry_start_decision_rsr_op08_selection_only_reviewer_form_rating_axis_contract_freeze_contract(op08_alias) is True

    op09_alias = rsr.build_p7_r54_ahr_post_dhr09_actual_local_review_retry_start_decision_rsr_op09_actual_local_only_review_lifecycle_state_capture(
        selection_only_reviewer_form_contract=op08_canonical,
        lifecycle_status_ref=rsr.P7_R54_AHR_POST_DHR09_RSR_REVIEW_LIFECYCLE_STATUS_COMPLETED_RECEIPT_REQUIRED_REF,
    )
    op09_canonical = rsr.build_p7_r54_ahr_post_dhr09_rsr_op09_actual_local_only_review_lifecycle_state_capture(
        selection_only_reviewer_form_contract=op08_canonical,
        lifecycle_status_ref=rsr.P7_R54_AHR_POST_DHR09_RSR_REVIEW_LIFECYCLE_STATUS_COMPLETED_RECEIPT_REQUIRED_REF,
    )
    assert op09_alias == op09_canonical
    assert rsr.assert_p7_r54_ahr_post_dhr09_actual_local_review_retry_start_decision_rsr_op09_actual_local_only_review_lifecycle_state_capture_contract(op09_alias) is True
