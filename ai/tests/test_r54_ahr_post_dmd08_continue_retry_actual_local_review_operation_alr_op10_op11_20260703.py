# -*- coding: utf-8 -*-
"""R54-AHR Post-DMD08 actual local review operation ALR-OP10/OP11 tests."""

from __future__ import annotations

from copy import deepcopy
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
from test_r54_ahr_post_dmd08_continue_retry_actual_local_review_operation_alr_op08_op09_20260703 import (
    _complete_receipt,
    _complete_row_sets,
    _op08,
    _op09,
)


def _op09_missing() -> dict[str, object]:
    return _op09(_op08())


def _op09_complete() -> dict[str, object]:
    return _op09(_op08(_complete_receipt()), rows=_complete_row_sets())


def _complete_disposal_purge_receipt(**overrides: object) -> dict[str, object]:
    receipt: dict[str, object] = {
        "schema_version": alr.P7_R54_AHR_POST_DMD08_ALR_DISPOSAL_PURGE_RECEIPT_SCHEMA_VERSION,
        "disposal_purge_receipt_ref": "disposal_purge_receipt_bodyfree_alr_op10_complete",
        "review_session_id": alr.P7_R54_AHR_POST_DMD08_ALR_DEFAULT_REVIEW_SESSION_ID,
        "body_full_packet_retained": False,
        "raw_input_retained": False,
        "comment_text_body_retained": False,
        "reviewer_note_body_retained": False,
        "question_text_retained": False,
        "draft_question_text_retained": False,
        "answer_text_retained": False,
        "local_path_included": False,
        "hash_included": False,
        "terminal_output_body_included": False,
        "disposal_purge_receipt_accepted": True,
        "body_free": True,
    }
    receipt.update(overrides)
    return receipt


def _op10(
    op09: dict[str, object] | None = None,
    *,
    receipt: dict[str, object] | None = None,
) -> dict[str, object]:
    return alr.build_p7_r54_ahr_post_dmd08_alr_op10_disposal_purge_receipt_expected_schema_guard(
        alr_op09_selection_only_rows_rating_question_need_expected_schema_guard=op09 or _op09_missing(),
        disposal_purge_receipt_bodyfree=receipt,
    )


def _op11(op10: dict[str, object] | None = None) -> dict[str, object]:
    return alr.build_p7_r54_ahr_post_dmd08_alr_op11_downstream_non_promotion_manual_decision_hold_finalizer(
        alr_op10_disposal_purge_receipt_expected_schema_guard=op10 or _op10(),
    )


def _assert_op10_does_not_create_execute_or_promote(material: dict[str, object]) -> None:
    for key in (
        "alr_op10_does_not_create_disposal_or_purge_receipt",
        "alr_op10_does_not_execute_disposal_or_purge",
        "alr_op10_does_not_generate_body_full_packet",
        "alr_op10_does_not_run_actual_local_human_review",
        "alr_op10_does_not_create_actual_rows",
        "alr_op10_does_not_execute_postcr22_ex_reentry_or_r52",
        "alr_op10_does_not_start_p5_p6_p8_p7_or_release",
        "alr_op10_does_not_change_api_db_rn_runtime_response_key",
    ):
        assert material[key] is True, key


def _assert_op11_does_not_execute_or_promote(material: dict[str, object]) -> None:
    for key in (
        "alr_op11_does_not_generate_body_full_packet",
        "alr_op11_does_not_run_actual_local_human_review",
        "alr_op11_does_not_create_actual_rows",
        "alr_op11_does_not_execute_disposal_or_purge",
        "alr_op11_does_not_execute_downstream_automatically",
        "alr_op11_does_not_execute_postcr22_ex_reentry_or_r52",
        "alr_op11_does_not_start_p5_p6_p8_p7_or_release",
        "alr_op11_does_not_change_api_db_rn_runtime_response_key",
    ):
        assert material[key] is True, key
    for key in (
        "manual_decision_auto_executes_downstream",
        "p5_final_allowed",
        "p6_start_allowed",
        "p8_start_allowed",
        "r52_actual_execution_started_here",
        "p7_complete",
        "release_allowed",
    ):
        assert material[key] is False, key


def test_alr_op10_defines_disposal_purge_receipt_expected_schema_without_creating_receipt_or_purge() -> None:
    material = _op10()

    assert set(material) == set(alr.P7_R54_AHR_POST_DMD08_ALR_OP10_REQUIRED_FIELD_REFS)
    assert material["schema_version"] == alr.P7_R54_AHR_POST_DMD08_ALR_OP10_SCHEMA_VERSION
    assert material["disposal_purge_receipt_guard_status_ref"] == alr.P7_R54_AHR_POST_DMD08_ALR_OP10_STATUS_RECEIPT_MISSING_REF
    assert material["disposal_purge_receipt_expected_schema_version_ref"] == alr.P7_R54_AHR_POST_DMD08_ALR_DISPOSAL_PURGE_RECEIPT_SCHEMA_VERSION
    assert tuple(material["disposal_purge_receipt_required_field_refs"]) == alr.P7_R54_AHR_POST_DMD08_ALR_OP10_RECEIPT_REQUIRED_FIELD_REFS
    assert tuple(material["disposal_purge_receipt_required_false_flag_refs"]) == alr.P7_R54_AHR_POST_DMD08_ALR_OP10_RECEIPT_REQUIRED_FALSE_FLAG_REFS
    assert material["disposal_purge_receipt_present"] is False
    assert material["disposal_purge_receipt_complete_candidate"] is False
    assert material["evidence_complete_candidate_after_disposal_guard"] is False
    assert material["disposal_purge_receipt_expected_schema_guard_ready"] is True
    assert material["next_required_step"] == alr.P7_R54_AHR_POST_DMD08_ALR_OP11_STEP_REF
    assert material["next_implementation_step"] == alr.P7_R54_AHR_POST_DMD08_ALR_OP11_STEP_REF
    _assert_op10_does_not_create_execute_or_promote(material)
    assert alr.assert_p7_r54_ahr_post_dmd08_alr_op10_disposal_purge_receipt_expected_schema_guard_contract(material) is True
    _assert_common_bodyfree_no_touch_no_promotion(material)


def test_alr_op10_accepts_complete_disposal_purge_receipt_only_as_bodyfree_receipt_guard() -> None:
    material = _op10(_op09_complete(), receipt=_complete_disposal_purge_receipt())

    assert material["disposal_purge_receipt_guard_status_ref"] == alr.P7_R54_AHR_POST_DMD08_ALR_OP10_STATUS_RECEIPT_ACCEPTED_REF
    assert material["disposal_purge_receipt_present"] is True
    assert material["disposal_purge_receipt_schema_version_valid"] is True
    assert material["disposal_purge_receipt_complete_candidate"] is True
    assert material["evidence_complete_candidate_after_disposal_guard"] is True
    assert material["disposal_purge_retention_false_complete"] is True
    assert all(value is True for value in material["disposal_purge_retention_false_pass_refs"].values())
    assert material["body_free_receipt_guard_passed"] is True
    assert material["actual_disposal_purge_executed_here"] is False
    assert material["next_required_step"] == alr.P7_R54_AHR_POST_DMD08_ALR_OP11_STEP_REF
    _assert_op10_does_not_create_execute_or_promote(material)
    assert alr.assert_p7_r54_ahr_post_dmd08_alr_op10_disposal_purge_receipt_expected_schema_guard_contract(material) is True
    _assert_common_bodyfree_no_touch_no_promotion(material)


def test_alr_op10_marks_incomplete_disposal_purge_receipt_without_promoting_complete() -> None:
    material = _op10(_op09_complete(), receipt=_complete_disposal_purge_receipt(disposal_purge_receipt_accepted=False))

    assert material["disposal_purge_receipt_guard_status_ref"] == alr.P7_R54_AHR_POST_DMD08_ALR_OP10_STATUS_RECEIPT_INCOMPLETE_REF
    assert material["disposal_purge_receipt_missing_or_incomplete"] is True
    assert material["disposal_purge_receipt_complete_candidate"] is False
    assert material["evidence_complete_candidate_after_disposal_guard"] is False
    assert material["body_free_receipt_guard_passed"] is True
    assert material["next_required_step"] == alr.P7_R54_AHR_POST_DMD08_ALR_OP11_STEP_REF
    assert alr.assert_p7_r54_ahr_post_dmd08_alr_op10_disposal_purge_receipt_expected_schema_guard_contract(material) is True
    _assert_common_bodyfree_no_touch_no_promotion(material)


def test_alr_op10_forbidden_body_payload_or_retention_flag_becomes_repair_without_body_value() -> None:
    bad_receipt = _complete_disposal_purge_receipt(raw_input="body-value-must-not-survive")
    material = _op10(_op09_complete(), receipt=bad_receipt)

    assert material["disposal_purge_receipt_guard_status_ref"] == alr.P7_R54_AHR_POST_DMD08_ALR_OP10_STATUS_RECEIPT_REPAIR_REQUIRED_REF
    assert material["bodyfree_disposal_boundary_repair_required"] is True
    assert material["disposal_purge_receipt_forbidden_payload_key_paths"] == ["disposal_purge_receipt_bodyfree.raw_input"]
    assert material["next_required_step"] == alr.P7_R54_AHR_POST_DMD08_ALR_NEXT_STEP_STOP_AND_REPAIR_BEFORE_OPERATION_REF
    assert "body-value-must-not-survive" not in repr(material)
    assert alr.assert_p7_r54_ahr_post_dmd08_alr_op10_disposal_purge_receipt_expected_schema_guard_contract(material) is True
    _assert_common_bodyfree_no_touch_no_promotion(material)

    retained = _op10(_op09_complete(), receipt=_complete_disposal_purge_receipt(body_full_packet_retained=True))
    assert retained["disposal_purge_receipt_guard_status_ref"] == alr.P7_R54_AHR_POST_DMD08_ALR_OP10_STATUS_RECEIPT_REPAIR_REQUIRED_REF
    assert retained["body_full_packet_retained"] is False
    assert retained["bodyfree_disposal_boundary_repair_required"] is True


def test_alr_op10_contract_rejects_manual_false_flag_tampering() -> None:
    material = _op10(_op09_complete(), receipt=_complete_disposal_purge_receipt())
    material["local_path_included"] = True

    with pytest.raises(ValueError):
        alr.assert_p7_r54_ahr_post_dmd08_alr_op10_disposal_purge_receipt_expected_schema_guard_contract(material)


def test_alr_op11_default_incomplete_evidence_returns_to_retry_or_start_without_downstream_promotion() -> None:
    material = _op11(_op10())

    assert set(material) == set(alr.P7_R54_AHR_POST_DMD08_ALR_OP11_REQUIRED_FIELD_REFS)
    assert material["schema_version"] == alr.P7_R54_AHR_POST_DMD08_ALR_OP11_SCHEMA_VERSION
    assert material["downstream_non_promotion_status_ref"] == alr.P7_R54_AHR_POST_DMD08_ALR_OP11_STATUS_ACTUAL_REVIEW_CONTINUE_OR_RETRY_REQUIRED_REF
    assert material["selected_action_ref"] == alr.P7_R54_AHR_POST_DMD08_ALR_ACTION_RETRY_OR_START_LOCAL_ONLY_REVIEW_REQUIRED_REF
    assert material["retry_or_start_required"] is True
    assert material["actual_local_review_operation_must_continue_or_retry"] is True
    assert material["manual_decision_hold_finalized"] is True
    assert material["downstream_non_promotion_finalizer_closed_bodyfree"] is True
    assert material["next_required_step"] == alr.P7_R54_AHR_POST_DMD08_ALR_NEXT_STEP_RETRY_OR_START_REVIEW_WITH_ALLOW_REF
    assert material["next_implementation_step"] == alr.P7_R54_AHR_POST_DMD08_ALR_OP12_STEP_REF
    _assert_op11_does_not_execute_or_promote(material)
    assert alr.assert_p7_r54_ahr_post_dmd08_alr_op11_downstream_non_promotion_manual_decision_hold_finalizer_contract(material) is True
    _assert_common_bodyfree_no_touch_no_promotion(material)


def test_alr_op11_complete_evidence_candidate_still_holds_downstream_manual_decision_without_auto_execution() -> None:
    op10 = _op10(_op09_complete(), receipt=_complete_disposal_purge_receipt())
    material = _op11(op10)

    assert material["downstream_non_promotion_status_ref"] == alr.P7_R54_AHR_POST_DMD08_ALR_OP11_STATUS_COMPLETE_RECEIPT_MANUAL_DECISION_REQUIRED_REF
    assert material["selected_action_ref"] == alr.P7_R54_AHR_POST_DMD08_ALR_ACTION_COMPLETE_RECEIPT_DOWNSTREAM_MANUAL_DECISION_REQUIRED_REF
    assert material["complete_receipt_manual_decision_required"] is True
    assert material["downstream_manual_decision_required"] is True
    assert material["complete_receipt_branch_requires_manual_decision"] is True
    assert material["manual_decision_auto_executes_downstream"] is False
    assert material["p5_p6_p8_r52_p7_release_auto_promotion_blocked"] is True
    assert material["next_required_step"] == alr.P7_R54_AHR_POST_DMD08_ALR_NEXT_STEP_DOWNSTREAM_MANUAL_DECISION_NO_AUTO_EXEC_REF
    _assert_op11_does_not_execute_or_promote(material)
    assert alr.assert_p7_r54_ahr_post_dmd08_alr_op11_downstream_non_promotion_manual_decision_hold_finalizer_contract(material) is True
    _assert_common_bodyfree_no_touch_no_promotion(material)


def test_alr_op11_preserves_repair_stop_from_op10_repair_path() -> None:
    op10 = _op10(_op09_complete(), receipt=_complete_disposal_purge_receipt(raw_input="body-value-must-not-survive"))
    material = _op11(op10)

    assert material["downstream_non_promotion_status_ref"] == alr.P7_R54_AHR_POST_DMD08_ALR_OP11_STATUS_REPAIR_STOP_REQUIRED_REF
    assert material["selected_action_ref"] == alr.P7_R54_AHR_POST_DMD08_ALR_ACTION_REPAIR_STOP_REQUIRED_REF
    assert material["repair_stop_required"] is True
    assert material["next_required_step"] == alr.P7_R54_AHR_POST_DMD08_ALR_NEXT_STEP_STOP_AND_REPAIR_BEFORE_OPERATION_REF
    assert "body-value-must-not-survive" not in repr(material)
    _assert_op11_does_not_execute_or_promote(material)
    assert alr.assert_p7_r54_ahr_post_dmd08_alr_op11_downstream_non_promotion_manual_decision_hold_finalizer_contract(material) is True
    _assert_common_bodyfree_no_touch_no_promotion(material)


def test_alr_op11_contract_rejects_any_downstream_promotion_flag_opened() -> None:
    material = _op11(_op10())
    material["p8_start_allowed"] = True

    with pytest.raises(ValueError):
        alr.assert_p7_r54_ahr_post_dmd08_alr_op11_downstream_non_promotion_manual_decision_hold_finalizer_contract(material)


def test_alr_op10_op11_aliases_match_full_design_title_names() -> None:
    op10 = alr.build_p7_r54_ahr_post_dmd08_continue_retry_actual_local_review_operation_alr_op10_disposal_purge_receipt_expected_schema_guard(
        alr_op09_selection_only_rows_rating_question_need_expected_schema_guard=_op09_missing(),
    )
    op11 = alr.build_p7_r54_ahr_post_dmd08_continue_retry_actual_local_review_operation_alr_op11_downstream_non_promotion_manual_decision_hold_finalizer(
        alr_op10_disposal_purge_receipt_expected_schema_guard=op10,
    )

    assert alr.assert_p7_r54_ahr_post_dmd08_continue_retry_actual_local_review_operation_alr_op10_disposal_purge_receipt_expected_schema_guard_contract(op10) is True
    assert alr.assert_p7_r54_ahr_post_dmd08_continue_retry_actual_local_review_operation_alr_op11_downstream_non_promotion_manual_decision_hold_finalizer_contract(op11) is True
    assert op10["disposal_purge_receipt_guard_status_ref"] == alr.P7_R54_AHR_POST_DMD08_ALR_OP10_STATUS_RECEIPT_MISSING_REF
    assert op11["downstream_non_promotion_status_ref"] == alr.P7_R54_AHR_POST_DMD08_ALR_OP11_STATUS_ACTUAL_REVIEW_CONTINUE_OR_RETRY_REQUIRED_REF


def test_alr_op10_op11_result_memo_exists_and_remains_bodyfree() -> None:
    result_memo = TEST_DIR / "R54_AHR_PostDMD08_ContinueRetryActualLocalOnlyHumanReviewOperation_ALR_OP00_OP11_Result_20260703.md"
    text = result_memo.read_text(encoding="utf-8")

    assert "ALR-OP10: disposal / purge receipt expected schema guard" in text
    assert "ALR-OP11: downstream non-promotion / manual decision hold finalizer" in text
    assert "actual_disposal_purge_execution: false" in text
    assert "manual_decision_auto_executes_downstream: false" in text
    assert "actual_local_human_review_execution: false" in text
    assert "p8_question_design: false" in text
    assert "release_decision: false" in text
    assert "raw_input:" not in text
    assert "question_text:" not in text
