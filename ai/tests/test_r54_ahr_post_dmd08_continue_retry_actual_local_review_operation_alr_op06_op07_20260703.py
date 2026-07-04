# -*- coding: utf-8 -*-
"""R54-AHR Post-DMD08 actual local review operation ALR-OP06/OP07 tests."""

from __future__ import annotations

from pathlib import Path
import sys

import pytest

TEST_DIR = Path(__file__).resolve().parent
if str(TEST_DIR) not in sys.path:
    sys.path.insert(0, str(TEST_DIR))

import emlis_ai_p7_r54_ahr_post_dmd08_continue_retry_actual_local_review_operation_20260703 as alr
from test_r54_ahr_post_dmd08_continue_retry_actual_local_review_operation_alr_op02_op03_20260703 import (
    _assert_common_bodyfree_no_touch_no_promotion,
)
from test_r54_ahr_post_dmd08_continue_retry_actual_local_review_operation_alr_op04_op05_20260703 import (
    _op02_complete,
    _op02_continuable,
    _op02_missing,
    _op02_repair_from_body_leak,
    _op04,
    _op05,
)


def _op05_retry() -> dict[str, object]:
    return _op05(_op04(_op02_missing()))


def _op05_continue() -> dict[str, object]:
    return _op05(_op04(_op02_continuable()))


def _op05_complete() -> dict[str, object]:
    return _op05(_op04(_op02_complete()))


def _op05_repair() -> dict[str, object]:
    return _op05(_op04(_op02_repair_from_body_leak()))


def _op06(op05: dict[str, object]) -> dict[str, object]:
    return alr.build_p7_r54_ahr_post_dmd08_alr_op06_explicit_local_only_allow_requirement_boundary(
        alr_op05_operation_state_machine_materialization=op05,
    )


def _op07(op06: dict[str, object]) -> dict[str, object]:
    return alr.build_p7_r54_ahr_post_dmd08_alr_op07_bodyfull_packet_request_bodyfree_envelope(
        alr_op06_explicit_local_only_allow_requirement_boundary=op06,
    )


def _assert_op06_no_allow_grant_or_execution(material: dict[str, object]) -> None:
    for key in (
        "operator_explicit_allow_receipt_created_here",
        "operator_explicit_allow_granted_here",
        "body_full_packet_generation_allowed_before_allow",
        "actual_human_review_execution_allowed_before_allow",
        "body_full_persistence_allowed",
        "external_export_allowed",
        "raw_body_persistence_allowed",
        "reviewer_free_text_allowed",
        "question_text_persistence_allowed",
        "local_path_persistence_allowed",
        "hash_persistence_allowed",
        "terminal_body_persistence_allowed",
        "body_full_packet_export_allowed",
        "body_full_packet_generation_allowed_after_op06",
        "actual_review_execution_allowed_after_op06",
    ):
        assert material[key] is False, key


def _assert_op07_no_packet_body_or_execution(material: dict[str, object]) -> None:
    for key in (
        "packet_generation_allowed_here",
        "body_full_packet_generation_allowed_here",
        "actual_review_execution_allowed_here",
        "body_full_packet_body_included",
        "packet_export_allowed",
        "body_full_packet_export_allowed",
        "raw_body_persistence_allowed",
        "reviewer_free_text_allowed",
        "question_text_persistence_allowed",
        "local_path_persistence_allowed",
        "hash_persistence_allowed",
        "terminal_body_persistence_allowed",
    ):
        assert material[key] is False, key
    assert all(value is False for value in material["forbidden_persistence_flags"].values())
    assert all(value is False for value in material["packet_body_not_included_flags"].values())
    for key in alr.P7_R54_AHR_POST_DMD08_ALR_OP07_PACKET_BODY_NOT_INCLUDED_FLAG_REFS:
        assert material[key] is False, key


@pytest.mark.parametrize(
    ("op05_builder", "expected_action_ref"),
    [
        (_op05_retry, alr.P7_R54_AHR_POST_DMD08_ALR_ACTION_RETRY_OR_START_LOCAL_ONLY_REVIEW_REQUIRED_REF),
        (_op05_continue, alr.P7_R54_AHR_POST_DMD08_ALR_ACTION_CONTINUE_EXISTING_LOCAL_ONLY_REVIEW_ALLOWED_REF),
    ],
)
def test_alr_op06_closes_explicit_allow_requirement_for_operation_plan_actions(op05_builder, expected_action_ref: str) -> None:
    material = _op06(op05_builder())

    assert set(material) == set(alr.P7_R54_AHR_POST_DMD08_ALR_OP06_REQUIRED_FIELD_REFS)
    assert material["schema_version"] == alr.P7_R54_AHR_POST_DMD08_ALR_OP06_SCHEMA_VERSION
    assert material["selected_action_ref"] == expected_action_ref
    assert material["local_only_allow_boundary_status_ref"] == alr.P7_R54_AHR_POST_DMD08_ALR_OP06_STATUS_READY_FOR_PACKET_REQUEST_REF
    assert material["explicit_local_only_allow_required"] is True
    assert material["operator_explicit_allow_receipt_required_next"] is True
    assert material["explicit_allow_boundary_closed_bodyfree"] is True
    assert material["packet_request_bodyfree_envelope_allowed_next"] is True
    assert material["alr_op06_ready_for_op07"] is True
    assert material["next_required_step"] == alr.P7_R54_AHR_POST_DMD08_ALR_OP07_STEP_REF
    assert material["next_implementation_step"] == alr.P7_R54_AHR_POST_DMD08_ALR_OP07_STEP_REF
    _assert_op06_no_allow_grant_or_execution(material)
    assert alr.assert_p7_r54_ahr_post_dmd08_alr_op06_explicit_local_only_allow_requirement_boundary_contract(material) is True
    _assert_common_bodyfree_no_touch_no_promotion(material)


@pytest.mark.parametrize(
    ("op05_builder", "expected_status_ref", "expected_next_required_step", "expected_next_implementation_step"),
    [
        (
            _op05_complete,
            alr.P7_R54_AHR_POST_DMD08_ALR_OP06_STATUS_NOT_APPLICABLE_DOWNSTREAM_MANUAL_DECISION_REF,
            alr.P7_R54_AHR_POST_DMD08_ALR_NEXT_STEP_DOWNSTREAM_MANUAL_DECISION_NO_AUTO_EXEC_REF,
            alr.P7_R54_AHR_POST_DMD08_ALR_OP11_STEP_REF,
        ),
        (
            _op05_repair,
            alr.P7_R54_AHR_POST_DMD08_ALR_OP06_STATUS_NOT_APPLICABLE_REPAIR_STOP_REF,
            alr.P7_R54_AHR_POST_DMD08_ALR_NEXT_STEP_STOP_AND_REPAIR_BEFORE_OPERATION_REF,
            alr.P7_R54_AHR_POST_DMD08_ALR_NEXT_STEP_STOP_AND_REPAIR_BEFORE_OPERATION_REF,
        ),
    ],
)
def test_alr_op06_keeps_packet_path_closed_for_complete_or_repair_paths(
    op05_builder,
    expected_status_ref: str,
    expected_next_required_step: str,
    expected_next_implementation_step: str,
) -> None:
    material = _op06(op05_builder())

    assert material["local_only_allow_boundary_status_ref"] == expected_status_ref
    assert material["explicit_local_only_allow_required"] is False
    assert material["operator_explicit_allow_receipt_required_next"] is False
    assert material["explicit_allow_boundary_closed_bodyfree"] is False
    assert material["packet_request_bodyfree_envelope_allowed_next"] is False
    assert material["alr_op06_ready_for_op07"] is False
    assert material["next_required_step"] == expected_next_required_step
    assert material["next_implementation_step"] == expected_next_implementation_step
    assert "body-value-must-not-survive" not in repr(material)
    _assert_op06_no_allow_grant_or_execution(material)
    assert alr.assert_p7_r54_ahr_post_dmd08_alr_op06_explicit_local_only_allow_requirement_boundary_contract(material) is True
    _assert_common_bodyfree_no_touch_no_promotion(material)


def test_alr_op06_contract_rejects_generation_allowed_before_allow() -> None:
    material = _op06(_op05_retry())
    material["body_full_packet_generation_allowed_before_allow"] = True

    with pytest.raises(ValueError):
        alr.assert_p7_r54_ahr_post_dmd08_alr_op06_explicit_local_only_allow_requirement_boundary_contract(material)


@pytest.mark.parametrize("op05_builder", [_op05_retry, _op05_continue])
def test_alr_op07_prepares_only_bodyfree_packet_request_envelope_for_ready_op06(op05_builder) -> None:
    material = _op07(_op06(op05_builder()))

    assert set(material) == set(alr.P7_R54_AHR_POST_DMD08_ALR_OP07_REQUIRED_FIELD_REFS)
    assert material["schema_version"] == alr.P7_R54_AHR_POST_DMD08_ALR_OP07_SCHEMA_VERSION
    assert material["packet_request_status_ref"] == alr.P7_R54_AHR_POST_DMD08_ALR_OP07_STATUS_PACKET_REQUEST_BODYFREE_ENVELOPE_READY_REF
    assert tuple(material["allowed_packet_request_status_refs"]) == alr.P7_R54_AHR_POST_DMD08_ALR_OP07_ALLOWED_STATUS_REFS
    assert material["packet_request_ref"]
    assert material["packet_request_bodyfree_envelope_ready"] is True
    assert material["body_full_packet_request_bodyfree_envelope_ready"] is True
    assert material["requested_case_count"] == alr.P7_R54_AHR_POST_DMD08_ALR_EXPECTED_ACTUAL_REVIEW_CASE_COUNT
    assert material["expected_review_unit_count"] == alr.P7_R54_AHR_POST_DMD08_ALR_EXPECTED_ACTUAL_REVIEW_CASE_COUNT
    assert material["reviewer_form_kind_ref"] == alr.P7_R54_AHR_POST_DMD08_ALR_OP07_REVIEWER_FORM_KIND_REF
    assert material["packet_generation_allowed_only_after_explicit_local_only_allow"] is True
    assert material["explicit_local_only_allow_required_before_packet_generation"] is True
    assert tuple(material["export_denylist_refs"]) == alr.P7_R54_AHR_POST_DMD08_ALR_OP07_PACKET_EXPORT_DENYLIST_REFS
    assert set(material["forbidden_persistence_flags"]) == set(alr.P7_R54_AHR_POST_DMD08_ALR_OP07_FORBIDDEN_PERSISTENCE_FLAG_REFS)
    assert set(material["packet_body_not_included_flags"]) == set(alr.P7_R54_AHR_POST_DMD08_ALR_OP07_PACKET_BODY_NOT_INCLUDED_FLAG_REFS)
    assert material["next_required_step"] == alr.P7_R54_AHR_POST_DMD08_ALR_OP08_STEP_REF
    assert material["next_implementation_step"] == alr.P7_R54_AHR_POST_DMD08_ALR_OP08_STEP_REF
    _assert_op07_no_packet_body_or_execution(material)
    assert alr.assert_p7_r54_ahr_post_dmd08_alr_op07_bodyfull_packet_request_bodyfree_envelope_contract(material) is True
    _assert_common_bodyfree_no_touch_no_promotion(material)


@pytest.mark.parametrize(
    ("op05_builder", "expected_status_ref", "expected_next_required_step", "expected_next_implementation_step"),
    [
        (
            _op05_complete,
            alr.P7_R54_AHR_POST_DMD08_ALR_OP07_STATUS_NOT_APPLICABLE_DOWNSTREAM_MANUAL_DECISION_REF,
            alr.P7_R54_AHR_POST_DMD08_ALR_NEXT_STEP_DOWNSTREAM_MANUAL_DECISION_NO_AUTO_EXEC_REF,
            alr.P7_R54_AHR_POST_DMD08_ALR_OP11_STEP_REF,
        ),
        (
            _op05_repair,
            alr.P7_R54_AHR_POST_DMD08_ALR_OP07_STATUS_NOT_APPLICABLE_REPAIR_STOP_REF,
            alr.P7_R54_AHR_POST_DMD08_ALR_NEXT_STEP_STOP_AND_REPAIR_BEFORE_OPERATION_REF,
            alr.P7_R54_AHR_POST_DMD08_ALR_NEXT_STEP_STOP_AND_REPAIR_BEFORE_OPERATION_REF,
        ),
    ],
)
def test_alr_op07_non_ready_paths_do_not_create_packet_request(
    op05_builder,
    expected_status_ref: str,
    expected_next_required_step: str,
    expected_next_implementation_step: str,
) -> None:
    material = _op07(_op06(op05_builder()))

    assert material["packet_request_status_ref"] == expected_status_ref
    assert material["packet_request_ref"] == ""
    assert material["requested_case_count"] == 0
    assert material["expected_review_unit_count"] == 0
    assert material["packet_request_bodyfree_envelope_ready"] is False
    assert material["packet_generation_allowed_only_after_explicit_local_only_allow"] is False
    assert material["next_required_step"] == expected_next_required_step
    assert material["next_implementation_step"] == expected_next_implementation_step
    assert "body-value-must-not-survive" not in repr(material)
    _assert_op07_no_packet_body_or_execution(material)
    assert alr.assert_p7_r54_ahr_post_dmd08_alr_op07_bodyfull_packet_request_bodyfree_envelope_contract(material) is True
    _assert_common_bodyfree_no_touch_no_promotion(material)


def test_alr_op07_contract_rejects_bodyfull_packet_body_inclusion() -> None:
    material = _op07(_op06(_op05_retry()))
    material["body_full_packet_body_included"] = True

    with pytest.raises(ValueError):
        alr.assert_p7_r54_ahr_post_dmd08_alr_op07_bodyfull_packet_request_bodyfree_envelope_contract(material)


def test_alr_op06_op07_aliases_match_full_design_title_names() -> None:
    op05 = _op05_retry()
    op06 = alr.build_p7_r54_ahr_post_dmd08_continue_retry_actual_local_review_operation_alr_op06_explicit_local_only_allow_requirement_boundary(
        alr_op05_operation_state_machine_materialization=op05,
    )
    op07 = alr.build_p7_r54_ahr_post_dmd08_continue_retry_actual_local_review_operation_alr_op07_bodyfull_packet_request_bodyfree_envelope(
        alr_op06_explicit_local_only_allow_requirement_boundary=op06,
    )

    assert alr.assert_p7_r54_ahr_post_dmd08_continue_retry_actual_local_review_operation_alr_op06_explicit_local_only_allow_requirement_boundary_contract(op06) is True
    assert alr.assert_p7_r54_ahr_post_dmd08_continue_retry_actual_local_review_operation_alr_op07_bodyfull_packet_request_bodyfree_envelope_contract(op07) is True
    assert op06["local_only_allow_boundary_status_ref"] == alr.P7_R54_AHR_POST_DMD08_ALR_OP06_STATUS_READY_FOR_PACKET_REQUEST_REF
    assert op07["packet_request_status_ref"] == alr.P7_R54_AHR_POST_DMD08_ALR_OP07_STATUS_PACKET_REQUEST_BODYFREE_ENVELOPE_READY_REF


def test_alr_op00_to_op07_retry_path_stays_bodyfree_without_packet_or_review_execution() -> None:
    op06 = _op06(_op05_retry())
    op07 = _op07(op06)

    assert tuple(op06["implemented_steps"]) == alr.P7_R54_AHR_POST_DMD08_ALR_OP06_IMPLEMENTED_STEPS
    assert tuple(op07["implemented_steps"]) == alr.P7_R54_AHR_POST_DMD08_ALR_OP07_IMPLEMENTED_STEPS
    assert tuple(op06["not_yet_implemented_steps"]) == alr.P7_R54_AHR_POST_DMD08_ALR_OP06_NOT_YET_IMPLEMENTED_STEPS
    assert tuple(op07["not_yet_implemented_steps"]) == alr.P7_R54_AHR_POST_DMD08_ALR_OP07_NOT_YET_IMPLEMENTED_STEPS
    for material in (op06, op07):
        assert material["not_claimed_boundary"]["actual_body_full_packet_generation"] is False
        assert material["not_claimed_boundary"]["actual_local_human_review_execution"] is False
        assert material["not_claimed_boundary"]["actual_rows_creation"] is False
        assert material["not_claimed_boundary"]["actual_disposal_purge_execution"] is False
        assert material["p8_start_allowed"] is False
        assert material["release_allowed"] is False


def test_alr_op06_op07_result_memo_exists_and_remains_bodyfree() -> None:
    result_memo = TEST_DIR / "R54_AHR_PostDMD08_ContinueRetryActualLocalOnlyHumanReviewOperation_ALR_OP00_OP07_Result_20260703.md"
    text = result_memo.read_text(encoding="utf-8")

    assert "ALR-OP06: explicit local-only allow requirement boundary" in text
    assert "ALR-OP07: body-full packet request body-free envelope" in text
    assert "body_full_packet_generated_here: false" in text
    assert "actual_local_human_review_execution: false" in text
    assert "p8_question_design: false" in text
    assert "release_decision: false" in text
    assert "raw_input:" not in text
    assert "comment_text:" not in text
