# -*- coding: utf-8 -*-
"""R54-AHR Post-CR22 actual local review evidence completion EX14-EX15 tests."""

from __future__ import annotations

from copy import deepcopy
from typing import Callable

import pytest

import emlis_ai_p7_r54_ahr_current_received_snapshot_actual_local_review_operation_20260628 as cr
import emlis_ai_p7_r54_ahr_post_cr22_actual_local_review_execution_evidence_completion_20260629 as ex


_FALSE_FLAG_ALLOW_EX14_EX15 = (
    "actual_rating_rows_materialized_here",
    "actual_question_need_observation_rows_materialized_here",
    "actual_disposal_receipt_materialized_here",
    "disposal_verified",
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
        reviewed_case_count=24,
        selection_row_count=24,
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


def _accepted_ex09(
    mutator: Callable[[list[dict[str, object]]], None] | None = None,
) -> dict[str, object]:
    ex07 = _accepted_ex07()
    rows = _actual_selection_rows_input(ex07, mutator=mutator)
    ex08 = ex.build_p7_r54_ahr_post_cr22_ex08_actual_selection_row_provenance_guard(
        actual_operation_receipt_intake=ex07,
        selection_result_rows=rows,
    )
    return ex.build_p7_r54_ahr_post_cr22_ex09_sanitized_review_result_rows_intake(
        actual_selection_row_provenance_guard=ex08,
        selection_result_rows=rows,
    )


def _accepted_ex09_ex10_ex11() -> tuple[dict[str, object], dict[str, object], dict[str, object]]:
    ex09 = _accepted_ex09()
    ex10 = ex.build_p7_r54_ahr_post_cr22_ex10_rating_row_normalization_threshold_summary(
        sanitized_review_result_rows_intake=ex09,
    )
    ex11 = ex.build_p7_r54_ahr_post_cr22_ex11_readfeel_execution_p5_p4_blocker_classification(
        rating_row_normalization_threshold_summary=ex10,
    )
    return ex09, ex10, ex11


def _accepted_ex13() -> dict[str, object]:
    ex09, ex10, ex11 = _accepted_ex09_ex10_ex11()
    ex12 = ex.build_p7_r54_ahr_post_cr22_ex12_question_need_observation_normalization(
        sanitized_review_result_rows_intake=ex09,
        rating_row_normalization_threshold_summary=ex10,
        readfeel_execution_p5_p4_blocker_classification=ex11,
    )
    return ex.build_p7_r54_ahr_post_cr22_ex13_rating_question_consistency_guard(
        rating_row_normalization_threshold_summary=ex10,
        readfeel_execution_p5_p4_blocker_classification=ex11,
        question_need_observation_normalization=ex12,
    )


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


def _accepted_ex14() -> dict[str, object]:
    return ex.build_p7_r54_ahr_post_cr22_ex14_disposal_purge_receipt_intake(
        rating_question_consistency_guard=_accepted_ex13(),
        disposal_receipt=_valid_disposal_receipt(),
    )


def test_ex14_blocks_without_ready_ex13_or_receipt_and_keeps_nonpromotion_false() -> None:
    material = ex.build_p7_r54_ahr_post_cr22_ex14_disposal_purge_receipt_intake()

    assert set(material) == set(ex.P7_R54_AHR_POST_CR22_EX14_REQUIRED_FIELD_REFS)
    assert material["schema_version"] == ex.P7_R54_AHR_POST_CR22_EX14_DISPOSAL_PURGE_RECEIPT_INTAKE_SCHEMA_VERSION
    assert material["operation_step_ref"] == ex.P7_R54_AHR_POST_CR22_EX14_STEP_REF
    assert material["disposal_purge_receipt_accepted"] is False
    assert material["disposal_purge_receipt_intake_status_ref"] == ex.P7_R54_AHR_POST_CR22_EX14_DISPOSAL_RECEIPT_BLOCKED_STATUS_REF
    assert "ex13_rating_question_consistency_guard_not_passed" in material["disposal_purge_receipt_blocker_refs"]
    assert "disposal_receipt_ref_missing" in material["disposal_purge_receipt_blocker_refs"]
    assert material["actual_disposal_receipt_materialized_here"] is False
    assert material["disposal_verified"] is False
    assert material["actual_review_evidence_complete"] is False
    assert material["next_required_step"] == ex.P7_R54_AHR_POST_CR22_EX14_DEFAULT_BLOCKED_NEXT_REQUIRED_STEP_REF
    _assert_bodyfree_no_touch_nonpromotion(material)
    assert ex.assert_p7_r54_ahr_post_cr22_ex14_disposal_purge_receipt_intake_contract(material) is True


def test_ex14_accepts_bodyfree_disposal_receipt_without_hash_path_notes_or_question_text() -> None:
    material = _accepted_ex14()

    assert set(material) == set(ex.P7_R54_AHR_POST_CR22_EX14_REQUIRED_FIELD_REFS)
    assert material["disposal_purge_receipt_accepted"] is True
    assert material["disposal_purge_receipt_intake_status_ref"] == ex.P7_R54_AHR_POST_CR22_EX14_DISPOSAL_RECEIPT_ACCEPTED_STATUS_REF
    assert material["disposal_purge_receipt_reason_refs"] == [ex.P7_R54_AHR_POST_CR22_EX14_READY_REASON_REF]
    assert material["disposal_purge_receipt_blocker_refs"] == []
    assert material["disposal_receipt_ref_present"] is True
    assert material["disposal_receipt_ref_is_bodyfree_ref"] is True
    assert material["disposal_status_is_body_purged"] is True
    assert material["packet_materialized_for_review"] is True
    assert material["body_removed"] is True
    assert material["content_hash_of_body_stored"] is False
    assert material["body_hash_stored"] is False
    assert material["local_absolute_path_included"] is False
    assert material["reviewer_notes_body_stored"] is False
    assert material["actual_disposal_receipt_materialized_here"] is True
    assert material["disposal_verified"] is True
    assert material["actual_review_evidence_complete"] is False
    assert material["p8_start_allowed"] is False
    assert tuple(material["implemented_steps"]) == ex.P7_R54_AHR_POST_CR22_EX14_IMPLEMENTED_STEPS
    assert tuple(material["not_yet_implemented_steps"]) == ex.P7_R54_AHR_POST_CR22_EX14_NOT_YET_IMPLEMENTED_STEPS
    assert material["next_required_step"] == ex.P7_R54_AHR_POST_CR22_EX15_STEP_REF
    _assert_bodyfree_no_touch_nonpromotion(material, allowed_true_false_flags=_FALSE_FLAG_ALLOW_EX14_EX15)
    assert ex.assert_p7_r54_ahr_post_cr22_ex14_disposal_purge_receipt_intake_contract(material) is True


@pytest.mark.parametrize(
    ("receipt_field", "value", "expected_blocker"),
    (
        ("body_removed", False, "body_removed_not_confirmed"),
        ("content_hash_of_body_stored", True, "content_hash_of_body_stored_must_be_false"),
        ("body_hash_stored", True, "body_hash_stored_must_be_false"),
        ("local_absolute_path_included", True, "local_absolute_path_included_must_be_false"),
        ("reviewer_notes_body_stored", True, "reviewer_notes_body_stored_must_be_false"),
        ("actual_source_ref", "helper_default_fixture_rows", "actual_source_ref_not_actual_local_disposal_receipt_bodyfree"),
    ),
)
def test_ex14_blocks_disposal_receipt_that_keeps_body_hash_path_notes_or_wrong_source(
    receipt_field: str, value: object, expected_blocker: str
) -> None:
    receipt = _valid_disposal_receipt()
    receipt[receipt_field] = value

    material = ex.build_p7_r54_ahr_post_cr22_ex14_disposal_purge_receipt_intake(
        rating_question_consistency_guard=_accepted_ex13(),
        disposal_receipt=receipt,
    )

    assert material["disposal_purge_receipt_accepted"] is False
    assert expected_blocker in material["disposal_purge_receipt_blocker_refs"]
    assert material["actual_disposal_receipt_materialized_here"] is False
    assert material["disposal_verified"] is False
    assert material["actual_review_evidence_complete"] is False
    assert ex.assert_p7_r54_ahr_post_cr22_ex14_disposal_purge_receipt_intake_contract(material) is True


@pytest.mark.parametrize(
    ("field", "value"),
    (
        ("actual_review_evidence_complete", True),
        ("p8_start_allowed", True),
        ("body_hash_stored", True),
        ("disposal_verified", False),
        ("next_required_step", "mutated_next_step"),
    ),
)
def test_ex14_contract_rejects_promotion_hash_or_disposal_mutations(field: str, value: object) -> None:
    material = _accepted_ex14()
    material[field] = value

    with pytest.raises(ValueError):
        ex.assert_p7_r54_ahr_post_cr22_ex14_disposal_purge_receipt_intake_contract(material)


def test_ex14_alias_builders_match_primary_contract() -> None:
    material = ex.build_p7_r54_ahr_post_cr22_actual_local_review_execution_evidence_completion_disposal_purge_receipt_intake_bodyfree(
        rating_question_consistency_guard=_accepted_ex13(),
        disposal_receipt=_valid_disposal_receipt(),
    )

    assert material["schema_version"] == ex.P7_R54_AHR_POST_CR22_EX14_DISPOSAL_PURGE_RECEIPT_INTAKE_SCHEMA_VERSION
    assert material["disposal_verified"] is True
    assert ex.assert_p7_r54_ahr_post_cr22_actual_local_review_execution_evidence_completion_disposal_purge_receipt_intake_bodyfree_contract(material) is True


def test_ex15_blocks_without_disposal_verified_and_keeps_nonpromotion_false() -> None:
    material = ex.build_p7_r54_ahr_post_cr22_ex15_final_no_body_leak_no_question_text_no_touch_validation()

    assert set(material) == set(ex.P7_R54_AHR_POST_CR22_EX15_REQUIRED_FIELD_REFS)
    assert material["schema_version"] == ex.P7_R54_AHR_POST_CR22_EX15_FINAL_NO_BODY_LEAK_NO_QUESTION_TEXT_NO_TOUCH_VALIDATION_SCHEMA_VERSION
    assert material["operation_step_ref"] == ex.P7_R54_AHR_POST_CR22_EX15_STEP_REF
    assert material["final_validation_evaluated"] is False
    assert material["final_validation_passed"] is False
    assert material["final_validation_status_ref"] == ex.P7_R54_AHR_POST_CR22_EX15_VALIDATION_BLOCKED_STATUS_REF
    assert "ex14_disposal_purge_receipt_not_accepted" in material["final_validation_step_blocker_refs"]
    assert material["actual_review_evidence_complete"] is False
    assert material["p8_start_allowed"] is False
    assert material["next_required_step"] == ex.P7_R54_AHR_POST_CR22_EX15_DEFAULT_BLOCKED_NEXT_REQUIRED_STEP_REF
    _assert_bodyfree_no_touch_nonpromotion(material)
    assert ex.assert_p7_r54_ahr_post_cr22_ex15_final_no_body_leak_no_question_text_no_touch_validation_contract(material) is True


def test_ex15_passes_clean_bodyfree_artifacts_without_completing_evidence_or_starting_p8() -> None:
    ex14 = _accepted_ex14()
    material = ex.build_p7_r54_ahr_post_cr22_ex15_final_no_body_leak_no_question_text_no_touch_validation(
        disposal_purge_receipt_intake=ex14,
        bodyfree_artifacts=[ex14],
    )

    assert set(material) == set(ex.P7_R54_AHR_POST_CR22_EX15_REQUIRED_FIELD_REFS)
    assert material["final_validation_evaluated"] is True
    assert material["final_validation_passed"] is True
    assert material["final_validation_status_ref"] == ex.P7_R54_AHR_POST_CR22_EX15_VALIDATION_PASSED_STATUS_REF
    assert material["final_validation_reason_refs"] == [ex.P7_R54_AHR_POST_CR22_EX15_READY_REASON_REF]
    assert material["final_validation_step_blocker_refs"] == []
    assert material["body_or_question_leak_refs"] == []
    assert material["path_or_hash_leak_refs"] == []
    assert material["contract_mutation_refs"] == []
    assert material["no_body_leak_validation_passed"] is True
    assert material["no_question_text_validation_passed"] is True
    assert material["no_touch_validation_passed"] is True
    assert material["no_local_path_or_hash_validation_passed"] is True
    assert material["actual_disposal_receipt_materialized_here"] is True
    assert material["disposal_verified"] is True
    assert material["actual_review_evidence_complete"] is False
    assert material["p8_start_allowed"] is False
    assert tuple(material["implemented_steps"]) == ex.P7_R54_AHR_POST_CR22_EX15_IMPLEMENTED_STEPS
    assert tuple(material["not_yet_implemented_steps"]) == ex.P7_R54_AHR_POST_CR22_EX15_NOT_YET_IMPLEMENTED_STEPS
    assert material["next_required_step"] == ex.P7_R54_AHR_POST_CR22_EX16_STEP_REF
    _assert_bodyfree_no_touch_nonpromotion(material, allowed_true_false_flags=_FALSE_FLAG_ALLOW_EX14_EX15)
    assert ex.assert_p7_r54_ahr_post_cr22_ex15_final_no_body_leak_no_question_text_no_touch_validation_contract(material) is True


@pytest.mark.parametrize(
    ("artifact_field", "value", "expected_ref_fragment"),
    (
        ("question_text_materialized_here", True, "question_text_materialized_here"),
        ("body_hash_stored", True, "body_hash_stored"),
        ("api_changed", True, "api_changed"),
    ),
)
def test_ex15_fails_when_scanned_artifact_contains_question_hash_or_no_touch_mutation(
    artifact_field: str, value: object, expected_ref_fragment: str
) -> None:
    ex14 = _accepted_ex14()
    artifact = deepcopy(ex14)
    artifact[artifact_field] = value

    material = ex.build_p7_r54_ahr_post_cr22_ex15_final_no_body_leak_no_question_text_no_touch_validation(
        disposal_purge_receipt_intake=ex14,
        bodyfree_artifacts=[artifact],
    )

    assert material["final_validation_evaluated"] is True
    assert material["final_validation_passed"] is False
    assert material["final_validation_status_ref"] == ex.P7_R54_AHR_POST_CR22_EX15_VALIDATION_FAILED_STATUS_REF
    combined_refs = (
        material["body_or_question_leak_refs"]
        + material["path_or_hash_leak_refs"]
        + material["contract_mutation_refs"]
    )
    assert any(expected_ref_fragment in ref for ref in combined_refs)
    assert material["actual_review_evidence_complete"] is False
    assert material["next_required_step"] == ex.P7_R54_AHR_POST_CR22_EX15_DEFAULT_BLOCKED_NEXT_REQUIRED_STEP_REF
    assert ex.assert_p7_r54_ahr_post_cr22_ex15_final_no_body_leak_no_question_text_no_touch_validation_contract(material) is True


@pytest.mark.parametrize(
    ("field", "value"),
    (
        ("actual_review_evidence_complete", True),
        ("p8_start_allowed", True),
        ("no_body_leak_validation_passed", False),
        ("final_validation_passed", False),
        ("next_required_step", "mutated_next_step"),
    ),
)
def test_ex15_contract_rejects_promotion_validation_or_next_step_mutations(field: str, value: object) -> None:
    ex14 = _accepted_ex14()
    material = ex.build_p7_r54_ahr_post_cr22_ex15_final_no_body_leak_no_question_text_no_touch_validation(
        disposal_purge_receipt_intake=ex14,
        bodyfree_artifacts=[ex14],
    )
    material[field] = value

    with pytest.raises(ValueError):
        ex.assert_p7_r54_ahr_post_cr22_ex15_final_no_body_leak_no_question_text_no_touch_validation_contract(material)


def test_ex15_alias_builders_match_primary_contract() -> None:
    ex14 = _accepted_ex14()
    material = ex.build_p7_r54_ahr_post_cr22_actual_local_review_execution_evidence_completion_final_no_body_leak_no_question_text_no_touch_validation_bodyfree(
        disposal_purge_receipt_intake=ex14,
        bodyfree_artifacts=[ex14],
    )

    assert material["schema_version"] == ex.P7_R54_AHR_POST_CR22_EX15_FINAL_NO_BODY_LEAK_NO_QUESTION_TEXT_NO_TOUCH_VALIDATION_SCHEMA_VERSION
    assert material["final_validation_passed"] is True
    assert ex.assert_p7_r54_ahr_post_cr22_actual_local_review_execution_evidence_completion_final_no_body_leak_no_question_text_no_touch_validation_bodyfree_contract(material) is True
