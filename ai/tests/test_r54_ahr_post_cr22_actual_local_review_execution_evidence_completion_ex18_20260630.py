# -*- coding: utf-8 -*-
"""R54-AHR Post-CR22 actual local review evidence completion EX18 tests."""

from __future__ import annotations

from copy import deepcopy
from typing import Callable

import pytest

import emlis_ai_p7_r54_ahr_current_received_snapshot_actual_local_review_operation_20260628 as cr
import emlis_ai_p7_r54_ahr_post_cr22_actual_local_review_execution_evidence_completion_20260629 as ex


_FALSE_FLAG_ALLOW_EX18 = (
    "actual_rating_rows_materialized_here",
    "actual_question_need_observation_rows_materialized_here",
    "actual_disposal_receipt_materialized_here",
    "disposal_verified",
    "actual_review_evidence_complete",
)


def _assert_bodyfree_no_touch_nonpromotion(
    material: dict[str, object], *, allowed_true_false_flags: tuple[str, ...] = ()
) -> None:
    assert material["body_free"] is True
    for key in ex.P7_R54_AHR_POST_CR22_REQUIRED_FALSE_FLAG_REFS:
        if key in allowed_true_false_flags:
            continue
        assert material[key] is False, key
    for marker_map_key in ("public_contract", "postcr22_no_touch_contract", "body_free_markers"):
        assert material[marker_map_key]
        assert all(value is False for value in material[marker_map_key].values()), marker_map_key
    for forbidden_key in ex.P7_R54_AHR_POST_CR22_FORBIDDEN_PAYLOAD_KEY_REFS:
        assert forbidden_key not in material, forbidden_key


def _ready_ex02() -> dict[str, object]:
    return ex.build_p7_r54_ahr_post_cr22_ex02_review_session_envelope_actual_source_guard_freeze()


def _ready_ex03() -> dict[str, object]:
    return ex.build_p7_r54_ahr_post_cr22_ex03_local_only_preflight_explicit_allow_packet_request_boundary(
        review_session_envelope_actual_source_guard=_ready_ex02(),
        explicit_allow_ref=ex.P7_R54_AHR_POST_CR22_EX03_DEFAULT_EXPLICIT_ALLOW_REF,
    )


def _ready_ex04() -> dict[str, object]:
    return ex.build_p7_r54_ahr_post_cr22_ex04_local_body_full_packet_generation_receipt_completeness_export_denylist_bodyfree_intake(
        local_only_preflight_explicit_allow_packet_request_boundary=_ready_ex03(),
        packet_generation_receipt_ref=ex.P7_R54_AHR_POST_CR22_EX04_DEFAULT_PACKET_GENERATION_RECEIPT_REF,
        packet_case_count=ex.P7_R54_AHR_POST_CR22_EX04_REQUIRED_CASE_COUNT,
        packet_completeness_scan_ref=ex.P7_R54_AHR_POST_CR22_EX04_DEFAULT_PACKET_COMPLETENESS_SCAN_REF,
        export_denylist_scan_ref=ex.P7_R54_AHR_POST_CR22_EX04_DEFAULT_EXPORT_DENYLIST_SCAN_REF,
        packet_completeness_passed=True,
        export_denylist_scan_passed=True,
    )


def _ready_ex05() -> dict[str, object]:
    return ex.build_p7_r54_ahr_post_cr22_ex05_reviewer_person_boundary_selection_only_form_freeze(
        local_body_full_packet_generation_receipt_completeness_export_denylist_bodyfree_intake=_ready_ex04(),
        reviewer_person_ref=ex.P7_R54_AHR_POST_CR22_EX05_DEFAULT_REVIEWER_PERSON_REF,
        reviewer_person_confirmed=True,
    )


def _ready_ex06() -> dict[str, object]:
    return ex.build_p7_r54_ahr_post_cr22_ex06_actual_local_only_human_review_execution_protocol(
        reviewer_person_boundary_selection_only_form_freeze=_ready_ex05(),
    )


def _accepted_ex07() -> dict[str, object]:
    return ex.build_p7_r54_ahr_post_cr22_ex07_actual_operation_receipt_intake(
        actual_local_only_human_review_execution_protocol=_ready_ex06(),
        operation_receipt_ref=ex.P7_R54_AHR_POST_CR22_EX07_DEFAULT_OPERATION_RECEIPT_REF,
        reviewer_person_ref=ex.P7_R54_AHR_POST_CR22_EX05_DEFAULT_REVIEWER_PERSON_REF,
        reviewer_local_only_read_receipt_present=True,
        review_started_at_bucket_ref=ex.P7_R54_AHR_POST_CR22_EX07_DEFAULT_REVIEW_STARTED_BUCKET_REF,
        review_completed_at_bucket_ref=ex.P7_R54_AHR_POST_CR22_EX07_DEFAULT_REVIEW_COMPLETED_BUCKET_REF,
        reviewed_case_count=ex.P7_R54_AHR_POST_CR22_EX04_REQUIRED_CASE_COUNT,
        selection_row_count=ex.P7_R54_AHR_POST_CR22_EX04_REQUIRED_CASE_COUNT,
    )


def _actual_selection_rows_input(
    ex07: dict[str, object],
    mutator: Callable[[list[dict[str, object]]], None] | None = None,
) -> list[dict[str, object]]:
    manifest = cr.build_p7_r54_ahr_cr04_current_24_case_manifest_refreeze()
    axis_scores = {axis_ref: 1.0 for axis_ref in cr.P7_R54_AHR_CR08_RATING_AXIS_REFS}
    plan_flags = {flag_ref: False for flag_ref in cr.P7_R54_AHR_CR10_PLAN_CANDIDATE_FLAG_REFS}
    rows: list[dict[str, object]] = []
    for index, case_row in enumerate(manifest["case_rows"], start=1):
        row: dict[str, object] = {
            "review_session_id": ex07["review_session_id"],
            "operation_receipt_ref": ex07["operation_receipt_ref"],
            "review_result_row_ref": f"postcr22_actual_review_result_row_{index:03d}",
            "case_ref_id": case_row["case_ref_id"],
            "blind_case_id": case_row["blind_case_id"],
            "packet_ref_id": case_row["packet_ref_id"],
            "reviewer_person_ref": ex07["reviewer_person_ref"],
            "reviewed_at_bucket_ref": f"postcr22_reviewed_bucket_20260629_{index:03d}",
            "axis_scores": dict(axis_scores),
            "axis_score_count": len(cr.P7_R54_AHR_CR08_RATING_AXIS_REFS),
            "verdict": "PASS",
            "sanitized_reason_ids": ["record_returned_as_natural_line"],
            "readfeel_blocker_ids": [],
            "execution_blocker_ids": [],
            "question_need_primary_class": "no_question_needed_emlis_can_observe",
            "ambiguity_kind_refs": ["no_material_ambiguity"],
            "one_question_fit_ref": "not_needed",
            "repair_required_refs": ["no_repair_required"],
            "plan_candidate_flags": dict(plan_flags),
            "row_source_ref": ex.P7_R54_AHR_POST_CR22_EX08_ALLOWED_ROW_SOURCE_REF,
            "row_created_by_helper": False,
            "row_created_for_unit_test": False,
            "row_is_synthetic_contract_fixture": False,
            "historical_row_reused": False,
            "selection_only": True,
            "selection_only_row": True,
            "body_free": True,
        }
        row.update({flag_ref: False for flag_ref in ex.P7_R54_AHR_POST_CR22_EX09_ROW_BODYFREE_FALSE_FLAG_REFS})
        rows.append(row)
    if mutator is not None:
        mutator(rows)
    return rows


def _mutate_first_row_to_clean_p8_candidate(rows: list[dict[str, object]]) -> None:
    rows[0]["question_need_primary_class"] = "question_may_reduce_overread_risk"
    rows[0]["one_question_fit_ref"] = "fits_one_question"
    rows[0]["plan_candidate_flags"] = dict(rows[0]["plan_candidate_flags"])
    rows[0]["plan_candidate_flags"]["p8_design_material_candidate"] = True
    rows[0]["plan_candidate_flags"]["plus_single_question_candidate_later"] = True
    rows[0]["sanitized_reason_ids"] = ["question_may_reduce_overread_risk_later"]


def _valid_disposal_receipt() -> dict[str, object]:
    return {
        "disposal_receipt_ref": ex.P7_R54_AHR_POST_CR22_EX14_DEFAULT_DISPOSAL_RECEIPT_REF,
        "disposal_status_ref": ex.P7_R54_AHR_POST_CR22_EX14_DEFAULT_DISPOSAL_STATUS_REF,
        "packet_materialized_for_review": True,
        "body_removed": True,
        "content_hash_of_body_stored": False,
        "body_hash_stored": False,
        "local_absolute_path_included": False,
        "reviewer_notes_body_stored": False,
        "pause_abort_status_ref": ex.P7_R54_AHR_POST_CR22_EX14_DEFAULT_PAUSE_ABORT_STATUS_REF,
        "retention_policy_ref": ex.P7_R54_AHR_POST_CR22_EX14_DEFAULT_RETENTION_POLICY_REF,
        "expiration_policy_ref": ex.P7_R54_AHR_POST_CR22_EX14_DEFAULT_EXPIRATION_POLICY_REF,
        "actual_source_ref": ex.P7_R54_AHR_POST_CR22_EX14_ALLOWED_ACTUAL_SOURCE_REF,
        "body_free": True,
    }


def _accepted_chain(
    mutator: Callable[[list[dict[str, object]]], None] | None = None,
) -> tuple[dict[str, object], dict[str, object], dict[str, object], dict[str, object]]:
    ex07 = _accepted_ex07()
    rows = _actual_selection_rows_input(ex07, mutator=mutator)
    ex08 = ex.build_p7_r54_ahr_post_cr22_ex08_actual_selection_row_provenance_guard(
        actual_operation_receipt_intake=ex07,
        selection_result_rows=rows,
    )
    ex09 = ex.build_p7_r54_ahr_post_cr22_ex09_sanitized_review_result_rows_intake(
        actual_selection_row_provenance_guard=ex08,
        selection_result_rows=rows,
    )
    ex10 = ex.build_p7_r54_ahr_post_cr22_ex10_rating_row_normalization_threshold_summary(
        sanitized_review_result_rows_intake=ex09,
    )
    ex11 = ex.build_p7_r54_ahr_post_cr22_ex11_readfeel_execution_p5_p4_blocker_classification(
        rating_row_normalization_threshold_summary=ex10,
    )
    ex12 = ex.build_p7_r54_ahr_post_cr22_ex12_question_need_observation_normalization(
        sanitized_review_result_rows_intake=ex09,
        rating_row_normalization_threshold_summary=ex10,
        readfeel_execution_p5_p4_blocker_classification=ex11,
    )
    ex13 = ex.build_p7_r54_ahr_post_cr22_ex13_rating_question_consistency_guard(
        rating_row_normalization_threshold_summary=ex10,
        readfeel_execution_p5_p4_blocker_classification=ex11,
        question_need_observation_normalization=ex12,
    )
    ex14 = ex.build_p7_r54_ahr_post_cr22_ex14_disposal_purge_receipt_intake(
        rating_question_consistency_guard=ex13,
        disposal_receipt=_valid_disposal_receipt(),
    )
    ex15 = ex.build_p7_r54_ahr_post_cr22_ex15_final_no_body_leak_no_question_text_no_touch_validation(
        disposal_purge_receipt_intake=ex14,
        bodyfree_artifacts=[ex14],
    )
    ex16 = ex.build_p7_r54_ahr_post_cr22_ex16_actual_review_evidence_complete_predicate(
        actual_operation_receipt_intake=ex07,
        sanitized_review_result_rows_intake=ex09,
        rating_row_normalization_threshold_summary=ex10,
        question_need_observation_normalization=ex12,
        rating_question_consistency_guard=ex13,
        final_no_body_leak_no_question_text_no_touch_validation=ex15,
    )
    ex17 = ex.build_p7_r54_ahr_post_cr22_ex17_p5_p6_p8_r52_candidate_only_separation(
        actual_review_evidence_complete_predicate=ex16,
        readfeel_execution_p5_p4_blocker_classification=ex11,
        question_need_observation_normalization=ex12,
        rating_question_consistency_guard=ex13,
    )
    return ex17, ex16, ex12, ex13


def _passed_ex18_validation_rows() -> list[dict[str, object]]:
    return ex.build_p7_r54_ahr_post_cr22_ex18_validation_command_rows_input(
        command_status_ref=ex.P7_R54_AHR_POST_CR22_EX18_COMMAND_STATUS_PASSED_REF,
        ran_here=True,
        green_claimed=True,
    )


def test_ex18_blocks_without_ex17_ready_and_without_validation_results() -> None:
    material = ex.build_p7_r54_ahr_post_cr22_ex18_validation_command_matrix_result_memo_next_decision_hold()

    assert set(material) == set(ex.P7_R54_AHR_POST_CR22_EX18_REQUIRED_FIELD_REFS)
    assert material["schema_version"] == ex.P7_R54_AHR_POST_CR22_EX18_VALIDATION_COMMAND_MATRIX_RESULT_MEMO_NEXT_DECISION_HOLD_SCHEMA_VERSION
    assert material["operation_step_ref"] == ex.P7_R54_AHR_POST_CR22_EX18_STEP_REF
    assert material["ex18_status_ref"] == ex.P7_R54_AHR_POST_CR22_EX18_BLOCKED_STATUS_REF
    assert material["ex18_ready"] is False
    assert "ex17_candidate_only_separation_not_ready_for_ex18" in material["ex18_blocker_refs"]
    assert "ex18_required_validation_command_not_passed" in material["ex18_blocker_refs"]
    assert material["validation_command_matrix_ready"] is False
    assert material["result_memo_ready"] is False
    assert material["actual_review_evidence_complete"] is False
    assert material["next_required_step"] == ex.P7_R54_AHR_POST_CR22_EX18_DEFAULT_BLOCKED_NEXT_REQUIRED_STEP_REF
    assert tuple(material["implemented_steps"]) == ex.P7_R54_AHR_POST_CR22_EX17_IMPLEMENTED_STEPS
    assert tuple(material["not_yet_implemented_steps"]) == ex.P7_R54_AHR_POST_CR22_EX17_NOT_YET_IMPLEMENTED_STEPS
    assert ex.assert_p7_r54_ahr_post_cr22_ex18_validation_command_matrix_result_memo_next_decision_hold_contract(material) is True
    _assert_bodyfree_no_touch_nonpromotion(material, allowed_true_false_flags=_FALSE_FLAG_ALLOW_EX18)


def test_ex18_ready_closes_result_memo_and_holds_next_decision_without_auto_promotion() -> None:
    ex17, _ex16, _ex12, _ex13 = _accepted_chain(mutator=_mutate_first_row_to_clean_p8_candidate)
    material = ex.build_p7_r54_ahr_post_cr22_ex18_validation_command_matrix_result_memo_next_decision_hold(
        candidate_only_separation=ex17,
        validation_command_rows=_passed_ex18_validation_rows(),
    )

    assert material["ex18_status_ref"] == ex.P7_R54_AHR_POST_CR22_EX18_READY_STATUS_REF
    assert material["ex18_ready"] is True
    assert material["ex18_blocker_refs"] == []
    assert material["validation_command_matrix_ready"] is True
    assert material["result_memo_ready"] is True
    assert material["actual_review_evidence_complete"] is True
    assert material["actual_human_review_executed_by_person"] is True
    assert material["actual_human_review_complete"] is False
    assert material["actual_human_review_run_here"] is False
    assert material["row_counts"]["reviewed_case_count"] == 24
    assert material["row_counts"]["sanitized_review_result_row_count"] == 24
    assert material["row_counts"]["rating_row_count"] == 24
    assert material["row_counts"]["question_need_observation_row_count"] == 24
    assert "P8_QUESTION_NEED_OBSERVATION_MATERIAL_CANDIDATE_ONLY" in material["candidate_only_decisions"]
    assert material["ex17_p8_question_need_observation_material_candidate_only"] is True
    assert material["next_decision_hold_required"] is True
    assert material["next_decision_auto_execution_allowed"] is False
    assert material["next_required_step"] == ex.P7_R54_AHR_POST_CR22_EX18_NEXT_DECISION_HOLD_REF
    assert material["p5_confirmed_final"] is False
    assert material["p5_final_allowed"] is False
    assert material["p6_start_allowed"] is False
    assert material["p8_start_allowed"] is False
    assert material["actual_r52_reintake_execution_confirmed"] is False
    assert material["release_allowed"] is False
    assert material["full_backend_suite_green"] is False
    assert material["rn_contract_green"] is False
    assert material["rn_real_device_modal_verified"] is False
    assert all(value is False for value in material["not_claimed_boundary"].values())
    assert tuple(material["implemented_steps"]) == ex.P7_R54_AHR_POST_CR22_EX18_IMPLEMENTED_STEPS
    assert tuple(material["not_yet_implemented_steps"]) == ex.P7_R54_AHR_POST_CR22_EX18_NOT_YET_IMPLEMENTED_STEPS
    assert ex.assert_p7_r54_ahr_post_cr22_ex18_validation_command_matrix_result_memo_next_decision_hold_contract(material) is True
    _assert_bodyfree_no_touch_nonpromotion(material, allowed_true_false_flags=_FALSE_FLAG_ALLOW_EX18)


@pytest.mark.parametrize(
    ("field", "bad_value"),
    (
        ("p5_confirmed_final", True),
        ("p5_final_allowed", True),
        ("p6_start_allowed", True),
        ("p8_start_allowed", True),
        ("actual_r52_reintake_execution_confirmed", True),
        ("release_allowed", True),
        ("full_backend_suite_green", True),
        ("rn_contract_green", True),
        ("rn_real_device_modal_verified", True),
        ("question_text_materialized_here", True),
        ("draft_question_text_materialized_here", True),
    ),
)
def test_ex18_contract_rejects_any_auto_promotion_or_question_text(field: str, bad_value: object) -> None:
    ex17, _ex16, _ex12, _ex13 = _accepted_chain(mutator=_mutate_first_row_to_clean_p8_candidate)
    material = ex.build_p7_r54_ahr_post_cr22_ex18_validation_command_matrix_result_memo_next_decision_hold(
        candidate_only_separation=ex17,
        validation_command_rows=_passed_ex18_validation_rows(),
    )
    mutated = deepcopy(material)
    mutated[field] = bad_value

    with pytest.raises(ValueError):
        ex.assert_p7_r54_ahr_post_cr22_ex18_validation_command_matrix_result_memo_next_decision_hold_contract(mutated)


def test_ex18_command_row_contract_is_bodyfree_and_rejects_promotion_claims() -> None:
    row = ex.build_p7_r54_ahr_post_cr22_ex18_validation_command_row(
        command_ref="ex18_target_postcr22_ex18_tests",
        command_status_ref=ex.P7_R54_AHR_POST_CR22_EX18_COMMAND_STATUS_PASSED_REF,
        ran_here=True,
        green_claimed=True,
    )

    assert row["body_free"] is True
    assert row["passed"] is True
    assert row["full_backend_suite_green_claimed"] is False
    assert ex.assert_p7_r54_ahr_post_cr22_ex18_validation_command_row_contract(row) is True

    mutated = deepcopy(row)
    mutated["p8_start_claimed"] = True
    with pytest.raises(ValueError):
        ex.assert_p7_r54_ahr_post_cr22_ex18_validation_command_row_contract(mutated)

    mutated = deepcopy(row)
    mutated["local_absolute_path_included"] = True
    with pytest.raises(ValueError):
        ex.assert_p7_r54_ahr_post_cr22_ex18_validation_command_row_contract(mutated)


def test_ex18_blocks_missing_duplicate_nonpassed_and_promotion_claim_command_rows() -> None:
    ex17, _ex16, _ex12, _ex13 = _accepted_chain()
    rows = _passed_ex18_validation_rows()
    rows = rows[:-1]
    duplicate = deepcopy(rows[0])
    duplicate["p8_start_claimed"] = True
    rows.append(duplicate)
    rows[1] = deepcopy(rows[1])
    rows[1]["command_status_ref"] = ex.P7_R54_AHR_POST_CR22_EX18_COMMAND_STATUS_FAILED_REF

    material = ex.build_p7_r54_ahr_post_cr22_ex18_validation_command_matrix_result_memo_next_decision_hold(
        candidate_only_separation=ex17,
        validation_command_rows=rows,
    )

    assert material["ex18_ready"] is False
    assert "ex18_required_validation_command_missing" in material["ex18_blocker_refs"]
    assert "ex18_validation_command_duplicate" in material["ex18_blocker_refs"]
    assert "ex18_required_validation_command_not_passed" in material["ex18_blocker_refs"]
    assert "ex18_validation_command_promotion_claim_detected" in material["ex18_blocker_refs"]
    assert material["validation_promotion_claim_command_refs"] == ["ex18_target_postcr22_ex18_tests"]
    assert material["actual_review_evidence_complete"] is False
    assert ex.assert_p7_r54_ahr_post_cr22_ex18_validation_command_matrix_result_memo_next_decision_hold_contract(material) is True


def test_ex18_contract_rejects_next_decision_auto_execution_or_changed_hold_ref() -> None:
    ex17, _ex16, _ex12, _ex13 = _accepted_chain()
    material = ex.build_p7_r54_ahr_post_cr22_ex18_validation_command_matrix_result_memo_next_decision_hold(
        candidate_only_separation=ex17,
        validation_command_rows=_passed_ex18_validation_rows(),
    )

    mutated = deepcopy(material)
    mutated["next_decision_auto_execution_allowed"] = True
    with pytest.raises(ValueError):
        ex.assert_p7_r54_ahr_post_cr22_ex18_validation_command_matrix_result_memo_next_decision_hold_contract(mutated)

    mutated = deepcopy(material)
    mutated["next_required_step"] = ex.P7_R54_AHR_POST_CR22_EX17_STEP_REF
    with pytest.raises(ValueError):
        ex.assert_p7_r54_ahr_post_cr22_ex18_validation_command_matrix_result_memo_next_decision_hold_contract(mutated)


def test_ex18_alias_matches_primary_builder_and_contract() -> None:
    ex17, _ex16, _ex12, _ex13 = _accepted_chain(mutator=_mutate_first_row_to_clean_p8_candidate)
    material = ex.build_p7_r54_ahr_post_cr22_actual_local_review_execution_evidence_completion_validation_command_matrix_result_memo_next_decision_hold_bodyfree(
        candidate_only_separation=ex17,
        validation_command_rows=_passed_ex18_validation_rows(),
    )

    assert material["schema_version"] == ex.P7_R54_AHR_POST_CR22_EX18_VALIDATION_COMMAND_MATRIX_RESULT_MEMO_NEXT_DECISION_HOLD_SCHEMA_VERSION
    assert material["ex18_ready"] is True
    assert material["p8_start_allowed"] is False
    assert material["actual_r52_reintake_execution_confirmed"] is False
    assert material["next_required_step"] == ex.P7_R54_AHR_POST_CR22_EX18_NEXT_DECISION_HOLD_REF
    assert ex.assert_p7_r54_ahr_post_cr22_actual_local_review_execution_evidence_completion_validation_command_matrix_result_memo_next_decision_hold_bodyfree_contract(material) is True
