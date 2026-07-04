# -*- coding: utf-8 -*-
"""R54-AHR Post-ALR12 explicit local-only review start/retry ELR-OP18/OP19 tests."""

from __future__ import annotations

from copy import deepcopy
from pathlib import Path
import sys

import pytest

TEST_DIR = Path(__file__).resolve().parent
if str(TEST_DIR) not in sys.path:
    sys.path.insert(0, str(TEST_DIR))

import emlis_ai_p7_r54_ahr_post_alr12_explicit_local_only_review_start_retry_operation_20260703 as elr
from test_r54_ahr_post_alr12_explicit_local_only_review_start_retry_operation_elr_op14_op15_20260703 import (
    _op15_passed,
)
from test_r54_ahr_post_alr12_explicit_local_only_review_start_retry_operation_elr_op16_op17_20260703 import (
    _assert_common_bodyfree_no_touch,
    _op17_ready,
)

_OP18_HOLD_CACHE: dict[str, object] | None = None
_OP19_CLOSED_CACHE: dict[str, object] | None = None


def _op17_waiting() -> dict[str, object]:
    op16_waiting = elr.build_p7_r54_ahr_post_alr12_elr_op16_actual_review_evidence_complete_predicate(
        op15_final_no_leak_no_touch_validation=_op15_passed(),
    )
    material = elr.build_p7_r54_ahr_post_alr12_elr_op17_dmd_compatible_actual_operation_evidence_receipt_adapter_handoff_candidate(
        op16_actual_review_evidence_complete_predicate=op16_waiting,
    )
    assert material["dmd_compatible_receipt_adapter_status_ref"] == elr.P7_R54_AHR_POST_ALR12_ELR_OP17_STATUS_WAITING_FOR_COMPLETE_EVIDENCE_REF
    assert elr.assert_p7_r54_ahr_post_alr12_elr_op17_dmd_compatible_actual_operation_evidence_receipt_adapter_handoff_candidate_contract(material) is True
    return material


def _op18_hold() -> dict[str, object]:
    global _OP18_HOLD_CACHE
    if _OP18_HOLD_CACHE is None:
        material = elr.build_p7_r54_ahr_post_alr12_elr_op18_downstream_non_promotion_manual_decision_hold(
            op17_dmd_compatible_actual_operation_evidence_receipt_adapter_handoff_candidate=_op17_ready(),
        )
        assert material["downstream_manual_decision_hold_status_ref"] == elr.P7_R54_AHR_POST_ALR12_ELR_OP18_STATUS_HELD_BODYFREE_REF
        assert elr.assert_p7_r54_ahr_post_alr12_elr_op18_downstream_non_promotion_manual_decision_hold_contract(material) is True
        _OP18_HOLD_CACHE = material
    return deepcopy(_OP18_HOLD_CACHE)


def _op19_closed() -> dict[str, object]:
    global _OP19_CLOSED_CACHE
    if _OP19_CLOSED_CACHE is None:
        material = elr.build_p7_r54_ahr_post_alr12_elr_op19_result_memo_validation_closure(
            op18_downstream_non_promotion_manual_decision_hold=_op18_hold(),
            target_tests_summary_optional={"status_ref": "elr_op18_op19_target_passed", "passed_count": 31},
            selected_regression_summary_optional={"status_ref": "selected_regression_passed", "passed_count": 390},
            compileall_summary_optional={"status_ref": "compileall_passed", "passed_count": 1},
            evidence_status_summary_optional={
                "alr_op12_intake_status_ref": elr.P7_R54_AHR_POST_ALR12_ELR_OP01_STATUS_ACCEPTED_RETRY_OR_START_REQUIRED_REF,
                "explicit_allow_status_ref": elr.P7_R54_AHR_POST_ALR12_ELR_OP02_STATUS_ACCEPTED_BODYFREE_REF,
                "actual_operation_receipt_status_ref": elr.P7_R54_AHR_POST_ALR12_ELR_OP09_STATUS_ACCEPTED_BODYFREE_REF,
                "sanitized_rows_status_ref": elr.P7_R54_AHR_POST_ALR12_ELR_OP10_STATUS_ACCEPTED_BODYFREE_REF,
                "rating_rows_status_ref": elr.P7_R54_AHR_POST_ALR12_ELR_OP11_STATUS_NORMALIZED_BODYFREE_REF,
                "question_need_rows_status_ref": elr.P7_R54_AHR_POST_ALR12_ELR_OP12_STATUS_NORMALIZED_BODYFREE_REF,
                "disposal_purge_receipt_status_ref": elr.P7_R54_AHR_POST_ALR12_ELR_OP14_STATUS_ACCEPTED_BODYFREE_REF,
                "final_validation_status_ref": elr.P7_R54_AHR_POST_ALR12_ELR_OP15_STATUS_PASSED_REF,
                "actual_review_evidence_complete_predicate_status_ref": elr.P7_R54_AHR_POST_ALR12_ELR_OP16_STATUS_COMPLETE_CANDIDATE_BODYFREE_REF,
            },
        )
        assert material["result_memo_validation_closure_status_ref"] == elr.P7_R54_AHR_POST_ALR12_ELR_OP19_STATUS_CLOSED_BODYFREE_REF
        assert elr.assert_p7_r54_ahr_post_alr12_elr_op19_result_memo_validation_closure_contract(material) is True
        _OP19_CLOSED_CACHE = material
    return deepcopy(_OP19_CLOSED_CACHE)


def test_elr_op18_holds_dmd_compatible_handoff_candidate_without_downstream_auto_execution() -> None:
    material = _op18_hold()

    assert set(material) == set(elr.P7_R54_AHR_POST_ALR12_ELR_OP18_REQUIRED_FIELD_REFS)
    assert material["schema_version"] == elr.P7_R54_AHR_POST_ALR12_ELR_OP18_SCHEMA_VERSION
    assert material["downstream_manual_decision_hold_status_ref"] == elr.P7_R54_AHR_POST_ALR12_ELR_OP18_STATUS_HELD_BODYFREE_REF
    assert material["op17_dmd_compatible_receipt_adapter_ready"] is True
    assert material["op17_dmd_compatible_receipt_handoff_candidate_ready"] is True
    assert material["downstream_manual_decision_hold_ready"] is True
    assert material["downstream_manual_decision_required"] is True
    assert material["downstream_manual_decision_required_without_auto_execution"] is True
    assert material["complete_candidate_held_without_downstream_execution"] is True
    assert material["manual_decision_auto_executes_downstream"] is False
    assert material["dmd_reexecution_started_here"] is False
    assert material["r52_actual_execution_started_here"] is False
    assert material["p5_final_allowed"] is False
    assert material["p6_start_allowed"] is False
    assert material["p8_start_allowed"] is False
    assert material["p7_complete"] is False
    assert material["release_allowed"] is False
    assert material["next_required_step"] == elr.P7_R54_AHR_POST_ALR12_ELR_OP19_STEP_REF
    assert material["elr_op18_blocker_refs"] == []
    assert elr.assert_p7_r54_ahr_post_alr12_elr_op18_downstream_non_promotion_manual_decision_hold_contract(material) is True
    _assert_common_bodyfree_no_touch(material)


def test_elr_op18_waits_when_op17_handoff_candidate_is_waiting_for_complete_evidence() -> None:
    material = elr.build_p7_r54_ahr_post_alr12_elr_op18_downstream_non_promotion_manual_decision_hold(
        op17_dmd_compatible_actual_operation_evidence_receipt_adapter_handoff_candidate=_op17_waiting(),
    )

    assert material["downstream_manual_decision_hold_status_ref"] == elr.P7_R54_AHR_POST_ALR12_ELR_OP18_STATUS_WAITING_FOR_HANDOFF_REF
    assert material["downstream_manual_decision_hold_waiting_for_handoff"] is True
    assert material["downstream_manual_decision_hold_ready"] is False
    assert material["downstream_manual_decision_required_without_auto_execution"] is False
    assert material["incomplete_branch_continue_or_waiting"] is True
    assert material["next_required_step"] == elr.P7_R54_AHR_POST_ALR12_ELR_NEXT_STEP_WAIT_FOR_COMPLETE_PREDICATE_EVIDENCE_REF
    assert elr.assert_p7_r54_ahr_post_alr12_elr_op18_downstream_non_promotion_manual_decision_hold_contract(material) is True
    _assert_common_bodyfree_no_touch(material)


def test_elr_op18_repairs_when_op17_handoff_candidate_contract_is_invalid() -> None:
    op17 = _op17_ready()
    op17["dmd_compatible_receipt_adapter_ready"] = False
    material = elr.build_p7_r54_ahr_post_alr12_elr_op18_downstream_non_promotion_manual_decision_hold(
        op17_dmd_compatible_actual_operation_evidence_receipt_adapter_handoff_candidate=op17,
    )

    assert material["downstream_manual_decision_hold_status_ref"] == elr.P7_R54_AHR_POST_ALR12_ELR_OP18_STATUS_REPAIR_REQUIRED_REF
    assert "elr_op18_op17_dmd_compatible_handoff_contract_invalid" in material["elr_op18_blocker_refs"]
    assert material["downstream_manual_decision_hold_ready"] is False
    assert material["next_required_step"] == elr.P7_R54_AHR_POST_ALR12_ELR_NEXT_STEP_REPAIR_DMD_COMPATIBLE_RECEIPT_ADAPTER_REF
    assert elr.assert_p7_r54_ahr_post_alr12_elr_op18_downstream_non_promotion_manual_decision_hold_contract(material) is True


def test_elr_op18_repairs_forbidden_payload_key_in_op17_without_leaking_body_value() -> None:
    op17 = _op17_ready()
    receipt = dict(op17["dmd_compatible_actual_operation_evidence_receipt_bodyfree"])
    receipt["question_text"] = "this body text must not leak"
    op17["dmd_compatible_actual_operation_evidence_receipt_bodyfree"] = receipt
    material = elr.build_p7_r54_ahr_post_alr12_elr_op18_downstream_non_promotion_manual_decision_hold(
        op17_dmd_compatible_actual_operation_evidence_receipt_adapter_handoff_candidate=op17,
    )

    assert material["downstream_manual_decision_hold_status_ref"] == elr.P7_R54_AHR_POST_ALR12_ELR_OP18_STATUS_REPAIR_REQUIRED_REF
    assert "elr_op18_op17_dmd_compatible_handoff_contract_invalid" in material["elr_op18_blocker_refs"]
    assert "elr_op18_op17_handoff_contains_forbidden_payload_key" in material["elr_op18_blocker_refs"]
    assert material["op17_dmd_compatible_receipt_forbidden_payload_key_path_count"] > 0
    assert "this body text must not leak" not in repr(material)
    assert elr.assert_p7_r54_ahr_post_alr12_elr_op18_downstream_non_promotion_manual_decision_hold_contract(material) is True


@pytest.mark.parametrize(
    ("field", "bad_value"),
    [
        ("downstream_manual_decision_hold_ready", False),
        ("downstream_manual_decision_required_without_auto_execution", False),
        ("manual_decision_hold_materialized_bodyfree", False),
        ("manual_decision_branch_ref", "R52_EXECUTION_ALLOWED"),
        ("manual_decision_auto_executes_downstream", True),
        ("dmd_reexecution_started_here", True),
        ("r52_actual_execution_started_here", True),
        ("p8_start_allowed", True),
        ("release_allowed", True),
        ("next_required_step", "P8_START"),
    ],
)
def test_elr_op18_contract_rejects_manual_hold_promotion_or_execution_mutations(field: str, bad_value: object) -> None:
    material = _op18_hold()
    material[field] = bad_value

    with pytest.raises(ValueError):
        elr.assert_p7_r54_ahr_post_alr12_elr_op18_downstream_non_promotion_manual_decision_hold_contract(material)


def test_elr_op19_closes_bodyfree_result_memo_validation_without_claiming_execution_or_release() -> None:
    material = _op19_closed()

    assert set(material) == set(elr.P7_R54_AHR_POST_ALR12_ELR_OP19_REQUIRED_FIELD_REFS)
    assert material["schema_version"] == elr.P7_R54_AHR_POST_ALR12_ELR_OP19_SCHEMA_VERSION
    assert material["result_memo_validation_closure_status_ref"] == elr.P7_R54_AHR_POST_ALR12_ELR_OP19_STATUS_CLOSED_BODYFREE_REF
    assert material["result_memo_bodyfree_closed"] is True
    assert material["result_memo_validation_closure_ready"] is True
    assert material["op18_downstream_manual_decision_hold_ready"] is True
    assert material["op18_downstream_manual_decision_required_without_auto_execution"] is True
    assert material["target_tests_passed_count"] == 31
    assert material["selected_regression_passed_count"] == 390
    assert material["compileall_passed"] is True
    assert material["raw_body_included"] is False
    assert material["question_text_included"] is False
    assert material["local_path_included"] is False
    assert material["body_hash_included"] is False
    assert material["terminal_output_body_included"] is False
    assert material["actual_body_full_packet_generation_verified_here"] is False
    assert material["actual_local_human_review_execution_verified_here"] is False
    assert material["actual_rows_created_verified_here"] is False
    assert material["actual_disposal_purge_execution_verified_here"] is False
    assert material["release_allowed"] is False
    assert material["manual_decision_auto_executes_downstream"] is False
    assert material["next_required_step"] == elr.P7_R54_AHR_POST_ALR12_ELR_NEXT_STEP_DOWNSTREAM_MANUAL_DECISION_AFTER_ELR_OP19_REF
    assert material["elr_op19_blocker_refs"] == []
    assert elr.assert_p7_r54_ahr_post_alr12_elr_op19_result_memo_validation_closure_contract(material) is True
    _assert_common_bodyfree_no_touch(material)


def test_elr_op19_waits_when_op18_manual_hold_is_waiting() -> None:
    op18_waiting = elr.build_p7_r54_ahr_post_alr12_elr_op18_downstream_non_promotion_manual_decision_hold(
        op17_dmd_compatible_actual_operation_evidence_receipt_adapter_handoff_candidate=_op17_waiting(),
    )
    material = elr.build_p7_r54_ahr_post_alr12_elr_op19_result_memo_validation_closure(
        op18_downstream_non_promotion_manual_decision_hold=op18_waiting,
    )

    assert material["result_memo_validation_closure_status_ref"] == elr.P7_R54_AHR_POST_ALR12_ELR_OP19_STATUS_WAITING_FOR_MANUAL_HOLD_REF
    assert material["result_memo_validation_waiting_for_manual_hold"] is True
    assert material["result_memo_bodyfree_closed"] is False
    assert material["next_required_step"] == elr.P7_R54_AHR_POST_ALR12_ELR_NEXT_STEP_WAIT_FOR_COMPLETE_PREDICATE_EVIDENCE_REF
    assert elr.assert_p7_r54_ahr_post_alr12_elr_op19_result_memo_validation_closure_contract(material) is True
    _assert_common_bodyfree_no_touch(material)


def test_elr_op19_repairs_when_op18_manual_hold_contract_is_invalid() -> None:
    op18 = _op18_hold()
    op18["downstream_manual_decision_hold_ready"] = False
    material = elr.build_p7_r54_ahr_post_alr12_elr_op19_result_memo_validation_closure(
        op18_downstream_non_promotion_manual_decision_hold=op18,
    )

    assert material["result_memo_validation_closure_status_ref"] == elr.P7_R54_AHR_POST_ALR12_ELR_OP19_STATUS_REPAIR_REQUIRED_REF
    assert "elr_op19_op18_manual_hold_contract_invalid" in material["elr_op19_blocker_refs"]
    assert material["result_memo_bodyfree_closed"] is False
    assert material["next_required_step"] == elr.P7_R54_AHR_POST_ALR12_ELR_OP18_STEP_REF
    assert elr.assert_p7_r54_ahr_post_alr12_elr_op19_result_memo_validation_closure_contract(material) is True


def test_elr_op19_repairs_forbidden_summary_material_without_leaking_body_value() -> None:
    material = elr.build_p7_r54_ahr_post_alr12_elr_op19_result_memo_validation_closure(
        op18_downstream_non_promotion_manual_decision_hold=_op18_hold(),
        target_tests_summary_optional={"status_ref": "target_tests_passed", "passed_count": 31, "raw_input": "secret body text"},
    )

    assert material["result_memo_validation_closure_status_ref"] == elr.P7_R54_AHR_POST_ALR12_ELR_OP19_STATUS_REPAIR_REQUIRED_REF
    assert "elr_op19_result_memo_forbidden_payload_key_detected" in material["elr_op19_blocker_refs"]
    assert material["result_memo_forbidden_payload_key_path_count"] > 0
    assert "secret body text" not in repr(material)
    assert elr.assert_p7_r54_ahr_post_alr12_elr_op19_result_memo_validation_closure_contract(material) is True


@pytest.mark.parametrize(
    ("field", "bad_value"),
    [
        ("result_memo_bodyfree_closed", False),
        ("result_memo_validation_closure_ready", False),
        ("raw_body_included", True),
        ("question_text_included", True),
        ("local_path_included", True),
        ("body_hash_included", True),
        ("terminal_output_body_included", True),
        ("actual_local_human_review_execution_verified_here", True),
        ("p8_question_design_started", True),
        ("p5_final_allowed", True),
        ("p8_start_allowed", True),
        ("release_allowed", True),
        ("manual_decision_auto_executes_downstream", True),
        ("next_required_step", "RELEASE_ALLOWED"),
    ],
)
def test_elr_op19_contract_rejects_closed_result_memo_execution_promotion_or_body_mutations(field: str, bad_value: object) -> None:
    material = _op19_closed()
    material[field] = bad_value

    with pytest.raises(ValueError):
        elr.assert_p7_r54_ahr_post_alr12_elr_op19_result_memo_validation_closure_contract(material)


def test_elr_op18_op19_full_operation_aliases_match_canonical_functions() -> None:
    op18 = elr.build_p7_r54_ahr_post_alr12_explicit_local_only_review_start_retry_operation_elr_op18_downstream_non_promotion_manual_decision_hold(
        op17_dmd_compatible_actual_operation_evidence_receipt_adapter_handoff_candidate=_op17_ready(),
    )
    assert elr.assert_p7_r54_ahr_post_alr12_explicit_local_only_review_start_retry_operation_elr_op18_downstream_non_promotion_manual_decision_hold_contract(op18) is True
    op19 = elr.build_p7_r54_ahr_post_alr12_explicit_local_only_review_start_retry_operation_elr_op19_result_memo_validation_closure(
        op18_downstream_non_promotion_manual_decision_hold=op18,
    )
    assert elr.assert_p7_r54_ahr_post_alr12_explicit_local_only_review_start_retry_operation_elr_op19_result_memo_validation_closure_contract(op19) is True
    assert op19["result_memo_validation_closure_status_ref"] == elr.P7_R54_AHR_POST_ALR12_ELR_OP19_STATUS_CLOSED_BODYFREE_REF


def test_elr_op18_op19_result_memo_is_bodyfree_and_current_scope_only() -> None:
    memo_path = TEST_DIR / "R54_AHR_PostALR12_ExplicitLocalOnlyReviewStartRetryOperation_ELR_OP00_OP19_Result_20260704.md"
    text = memo_path.read_text(encoding="utf-8")

    assert "ELR-OP18" in text
    assert "ELR-OP19" in text
    assert "downstream non-promotion manual decision hold: implemented" in text
    assert "result memo / validation closure: implemented" in text
    assert "manual_decision_auto_executes_downstream: false" in text
    assert "DMD re-execution: not performed" in text
    assert "R52 actual execution: not started" in text
    assert "P5/P6/P8/R52/P7/release auto-promotion: blocked" in text
    assert "release_allowed: false" in text
    assert "raw_input:" not in text
    assert "comment_text:" not in text
    assert "question_text:" not in text
    assert "local_path:" not in text
    assert "body_hash:" not in text
    assert "terminal_output:" not in text
