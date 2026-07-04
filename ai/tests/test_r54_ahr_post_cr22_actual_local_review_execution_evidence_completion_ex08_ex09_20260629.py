# -*- coding: utf-8 -*-
"""R54-AHR Post-CR22 actual local review evidence completion EX08-EX09 tests."""

from __future__ import annotations

from copy import deepcopy

import pytest

import emlis_ai_p7_r54_ahr_current_received_snapshot_actual_local_review_operation_20260628 as cr
import emlis_ai_p7_r54_ahr_post_cr22_actual_local_review_execution_evidence_completion_20260629 as ex


def _assert_bodyfree_no_touch_nonpromotion(material: dict[str, object]) -> None:
    assert material["body_free"] is True
    for key in ex.P7_R54_AHR_POST_CR22_REQUIRED_FALSE_FLAG_REFS:
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


def _actual_selection_rows_input(ex07: dict[str, object]) -> list[dict[str, object]]:
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
    return rows


def _accepted_ex08() -> dict[str, object]:
    ex07 = _accepted_ex07()
    return ex.build_p7_r54_ahr_post_cr22_ex08_actual_selection_row_provenance_guard(
        actual_operation_receipt_intake=ex07,
        selection_result_rows=_actual_selection_rows_input(ex07),
    )


def _accepted_ex09() -> dict[str, object]:
    ex07 = _accepted_ex07()
    rows = _actual_selection_rows_input(ex07)
    ex08 = ex.build_p7_r54_ahr_post_cr22_ex08_actual_selection_row_provenance_guard(
        actual_operation_receipt_intake=ex07,
        selection_result_rows=rows,
    )
    return ex.build_p7_r54_ahr_post_cr22_ex09_sanitized_review_result_rows_intake(
        actual_selection_row_provenance_guard=ex08,
        selection_result_rows=rows,
    )


def test_ex08_blocks_without_selection_rows_even_after_operation_receipt() -> None:
    material = ex.build_p7_r54_ahr_post_cr22_ex08_actual_selection_row_provenance_guard(
        actual_operation_receipt_intake=_accepted_ex07(),
    )

    assert set(material) == set(ex.P7_R54_AHR_POST_CR22_EX08_REQUIRED_FIELD_REFS)
    assert material["schema_version"] == ex.P7_R54_AHR_POST_CR22_EX08_ACTUAL_SELECTION_ROW_PROVENANCE_GUARD_SCHEMA_VERSION
    assert material["operation_step_ref"] == ex.P7_R54_AHR_POST_CR22_EX08_STEP_REF
    assert material["ex07_operation_receipt_accepted"] is True
    assert material["selection_row_provenance_guard_passed"] is False
    assert "selection_result_rows_input_missing" in material["selection_row_provenance_guard_blocker_refs"]
    assert "selection_result_row_count_not_24" in material["selection_row_provenance_guard_blocker_refs"]
    assert material["selection_row_provenance_rows"] == []
    assert material["actual_rows_source_guard_passed"] is False
    assert material["actual_human_review_executed_by_person"] is False
    assert material["actual_review_evidence_complete"] is False
    assert tuple(material["implemented_steps"]) == ex.P7_R54_AHR_POST_CR22_EX07_IMPLEMENTED_STEPS
    assert tuple(material["not_yet_implemented_steps"]) == ex.P7_R54_AHR_POST_CR22_EX07_NOT_YET_IMPLEMENTED_STEPS
    assert material["next_required_step"] == ex.P7_R54_AHR_POST_CR22_EX08_DEFAULT_BLOCKED_NEXT_REQUIRED_STEP_REF
    _assert_bodyfree_no_touch_nonpromotion(material)
    assert ex.assert_p7_r54_ahr_post_cr22_ex08_actual_selection_row_provenance_guard_contract(material) is True


def test_ex08_accepts_actual_person_selection_row_provenance_without_sanitizing_rows() -> None:
    material = _accepted_ex08()

    assert set(material) == set(ex.P7_R54_AHR_POST_CR22_EX08_REQUIRED_FIELD_REFS)
    assert material["selection_row_provenance_guard_status_ref"] == ex.P7_R54_AHR_POST_CR22_EX08_PROVENANCE_GUARD_ACCEPTED_STATUS_REF
    assert material["selection_row_provenance_guard_passed"] is True
    assert material["selection_row_provenance_guard_blocker_refs"] == []
    assert material["selection_row_provenance_row_count"] == 24
    assert material["row_source_refs_observed"] == [ex.P7_R54_AHR_POST_CR22_EX08_ALLOWED_ROW_SOURCE_REF]
    assert material["row_source_refs_all_actual_person_selection_only_rows"] is True
    assert material["helper_default_rows_detected"] is False
    assert material["unit_test_rows_detected"] is False
    assert material["synthetic_contract_rows_detected"] is False
    assert material["historical_rows_detected"] is False
    assert material["review_session_id_matches_all_rows"] is True
    assert material["operation_receipt_ref_matches_all_rows"] is True
    assert material["reviewer_person_ref_matches_all_rows"] is True
    assert material["rows_match_24_case_manifest"] is True
    assert material["rows_bodyfree_only"] is True
    assert material["rows_selection_only"] is True
    assert material["rows_have_no_body_or_question_or_path_or_hash"] is True
    assert material["actual_rows_source_guard_passed"] is True
    assert material["actual_selection_row_provenance_checked_here"] is True
    assert material["sanitized_selection_only_result_rows_intaken_here"] is False
    assert material["actual_sanitized_review_result_rows_intaken_here"] is False
    assert material["actual_rating_rows_materialized_here"] is False
    assert material["actual_question_need_observation_rows_materialized_here"] is False
    assert material["actual_review_evidence_complete"] is False
    assert tuple(material["implemented_steps"]) == ex.P7_R54_AHR_POST_CR22_EX08_IMPLEMENTED_STEPS
    assert tuple(material["not_yet_implemented_steps"]) == ex.P7_R54_AHR_POST_CR22_EX08_NOT_YET_IMPLEMENTED_STEPS
    assert material["next_required_step"] == ex.P7_R54_AHR_POST_CR22_EX09_STEP_REF
    _assert_bodyfree_no_touch_nonpromotion(material)
    assert ex.assert_p7_r54_ahr_post_cr22_ex08_actual_selection_row_provenance_guard_contract(material) is True


@pytest.mark.parametrize(
    ("field", "value", "expected_blocker"),
    (
        ("row_source_ref", "helper_default_fixture_rows", "selection_row_source_ref_forbidden"),
        ("row_source_ref", "unit_test_contract_rows", "selection_row_source_ref_forbidden"),
        ("row_source_ref", "synthetic_bodyfree_rows", "selection_row_source_ref_forbidden"),
        ("row_source_ref", "historical_ahr_260_83_256_169_rows", "selection_row_source_ref_forbidden"),
        ("row_source_ref", "rows_without_person_read_receipt", "selection_row_source_ref_forbidden"),
        ("row_created_by_helper", True, "selection_row_created_by_helper"),
        ("row_created_for_unit_test", True, "selection_row_created_for_unit_test"),
        ("row_is_synthetic_contract_fixture", True, "selection_row_is_synthetic_contract_fixture"),
        ("historical_row_reused", True, "selection_row_historical_reused"),
        ("review_session_id", "wrong_session", "selection_row_review_session_id_mismatch"),
        ("operation_receipt_ref", "wrong_receipt", "selection_row_operation_receipt_ref_mismatch"),
        ("reviewer_person_ref", "wrong_person", "selection_row_reviewer_person_ref_mismatch"),
        ("selection_only", False, "selection_row_selection_only_false"),
        ("body_free", False, "selection_row_body_free_false"),
        ("question_text_included", True, "selection_row_bodyfree_forbidden_flag_not_false"),
        ("local_absolute_path_included", True, "selection_row_bodyfree_forbidden_flag_not_false"),
    ),
)
def test_ex08_blocks_non_actual_or_mismatched_row_provenance(
    field: str, value: object, expected_blocker: str
) -> None:
    ex07 = _accepted_ex07()
    rows = _actual_selection_rows_input(ex07)
    rows[0][field] = value

    material = ex.build_p7_r54_ahr_post_cr22_ex08_actual_selection_row_provenance_guard(
        actual_operation_receipt_intake=ex07,
        selection_result_rows=rows,
    )

    assert material["selection_row_provenance_guard_passed"] is False
    assert expected_blocker in material["selection_row_provenance_guard_blocker_refs"]
    assert material["selection_row_provenance_rows"] == []
    assert material["actual_rows_source_guard_passed"] is False
    assert material["actual_human_review_executed_by_person"] is False
    assert material["actual_review_evidence_complete"] is False
    assert ex.assert_p7_r54_ahr_post_cr22_ex08_actual_selection_row_provenance_guard_contract(material) is True


def test_ex08_rejects_path_shaped_row_refs_without_echoing_path_values() -> None:
    ex07 = _accepted_ex07()
    rows = _actual_selection_rows_input(ex07)
    rows[0]["review_result_row_ref"] = "/tmp/secret-selection-row"

    material = ex.build_p7_r54_ahr_post_cr22_ex08_actual_selection_row_provenance_guard(
        actual_operation_receipt_intake=ex07,
        selection_result_rows=rows,
    )

    assert material["selection_row_provenance_guard_passed"] is False
    assert "selection_row_ref_must_be_bodyfree_ref_not_path" in material["selection_row_provenance_guard_blocker_refs"]
    assert material["selection_row_provenance_rows"] == []
    assert "secret-selection-row" not in repr(material)
    assert ex.assert_p7_r54_ahr_post_cr22_ex08_actual_selection_row_provenance_guard_contract(material) is True


@pytest.mark.parametrize(
    ("field", "value"),
    (
        ("selection_row_provenance_guard_passed", False),
        ("actual_rows_source_guard_passed", False),
        ("actual_human_review_executed_by_person", False),
        ("sanitized_selection_only_result_rows_intaken_here", True),
        ("actual_sanitized_review_result_rows_intaken_here", True),
        ("actual_rating_rows_materialized_here", True),
        ("actual_question_need_observation_rows_materialized_here", True),
        ("actual_review_evidence_complete", True),
        ("p8_start_allowed", True),
        ("release_allowed", True),
        ("next_required_step", "mutated_next_step"),
    ),
)
def test_ex08_contract_rejects_sanitized_rows_evidence_or_promotion_mutations(field: str, value: object) -> None:
    material = deepcopy(_accepted_ex08())
    material[field] = value

    with pytest.raises(ValueError):
        ex.assert_p7_r54_ahr_post_cr22_ex08_actual_selection_row_provenance_guard_contract(material)


def test_ex09_blocks_when_ex08_provenance_guard_is_not_ready() -> None:
    ex07 = _accepted_ex07()
    rows = _actual_selection_rows_input(ex07)
    blocked_ex08 = ex.build_p7_r54_ahr_post_cr22_ex08_actual_selection_row_provenance_guard(
        actual_operation_receipt_intake=ex07,
        selection_result_rows=[],
    )
    material = ex.build_p7_r54_ahr_post_cr22_ex09_sanitized_review_result_rows_intake(
        actual_selection_row_provenance_guard=blocked_ex08,
        selection_result_rows=rows,
    )

    assert set(material) == set(ex.P7_R54_AHR_POST_CR22_EX09_REQUIRED_FIELD_REFS)
    assert material["schema_version"] == ex.P7_R54_AHR_POST_CR22_EX09_SANITIZED_REVIEW_RESULT_ROWS_INTAKE_SCHEMA_VERSION
    assert material["operation_step_ref"] == ex.P7_R54_AHR_POST_CR22_EX09_STEP_REF
    assert material["ex08_selection_row_provenance_guard_passed"] is False
    assert material["sanitized_review_result_rows_intake_ready"] is False
    assert "ex08_selection_row_provenance_guard_not_accepted" in material["sanitized_review_result_rows_intake_blocker_refs"]
    assert material["review_result_rows"] == []
    assert material["actual_sanitized_review_result_rows_intaken_here"] is False
    assert material["actual_review_evidence_complete"] is False
    assert material["next_required_step"] == ex.P7_R54_AHR_POST_CR22_EX09_DEFAULT_BLOCKED_NEXT_REQUIRED_STEP_REF
    _assert_bodyfree_no_touch_nonpromotion(material)
    assert ex.assert_p7_r54_ahr_post_cr22_ex09_sanitized_review_result_rows_intake_contract(material) is True


def test_ex09_accepts_and_sanitizes_24_actual_selection_rows_without_completing_evidence() -> None:
    material = _accepted_ex09()

    assert set(material) == set(ex.P7_R54_AHR_POST_CR22_EX09_REQUIRED_FIELD_REFS)
    assert material["sanitized_review_result_rows_intake_status_ref"] == ex.P7_R54_AHR_POST_CR22_EX09_SANITIZED_ROWS_ACCEPTED_STATUS_REF
    assert material["sanitized_review_result_rows_intake_ready"] is True
    assert material["sanitized_review_result_rows_intake_blocker_refs"] == []
    assert material["received_selection_row_count"] == 24
    assert material["selection_result_row_count"] == 24
    assert material["sanitized_review_result_row_count"] == 24
    assert material["review_result_row_ref_count"] == 24
    assert material["case_ref_ids_unique"] is True
    assert material["blind_case_ids_unique"] is True
    assert material["packet_ref_ids_unique"] is True
    assert material["reviewed_at_bucket_refs_present"] is True
    assert tuple(material["axis_refs"]) == cr.P7_R54_AHR_CR08_RATING_AXIS_REFS
    assert material["axis_score_count_per_row"] == 6
    assert material["rows_match_24_case_manifest"] is True
    assert material["rows_bodyfree_only"] is True
    assert material["rows_selection_only"] is True
    assert material["rows_have_actual_person_selection_only_provenance"] is True
    assert material["rows_have_required_axis_scores"] is True
    assert material["rows_have_allowed_verdict_refs"] is True
    assert material["rows_have_allowed_question_observation_refs"] is True
    assert material["rows_have_no_body_or_question_or_path_or_hash"] is True
    assert material["sanitized_selection_only_result_rows_intaken_here"] is True
    assert material["actual_sanitized_review_result_rows_intaken_here"] is True
    assert material["actual_human_review_executed_by_person"] is True
    assert material["actual_selection_rows_created_here"] is False
    assert material["actual_rating_rows_materialized_here"] is False
    assert material["actual_question_need_observation_rows_materialized_here"] is False
    assert material["actual_disposal_receipt_materialized_here"] is False
    assert material["actual_review_evidence_complete"] is False
    assert material["p8_question_implementation_spec_finalized_here"] is False
    assert material["p8_start_allowed"] is False
    assert material["rating_row_normalization_allowed_next"] is True
    assert tuple(material["implemented_steps"]) == ex.P7_R54_AHR_POST_CR22_EX09_IMPLEMENTED_STEPS
    assert tuple(material["not_yet_implemented_steps"]) == ex.P7_R54_AHR_POST_CR22_EX09_NOT_YET_IMPLEMENTED_STEPS
    assert material["next_required_step"] == ex.P7_R54_AHR_POST_CR22_EX10_STEP_REF
    for row in material["review_result_rows"]:
        assert row["schema_version"] == ex.P7_R54_AHR_POST_CR22_EX09_SELECTION_RESULT_ROW_SCHEMA_VERSION
        assert row["row_source_ref"] == ex.P7_R54_AHR_POST_CR22_EX08_ALLOWED_ROW_SOURCE_REF
        assert row["row_created_by_helper"] is False
        assert row["row_created_for_unit_test"] is False
        assert row["row_is_synthetic_contract_fixture"] is False
        assert row["historical_row_reused"] is False
        assert row["body_free"] is True
        assert row["selection_only"] is True
        assert row["selection_only_row"] is True
        assert all(row[flag_ref] is False for flag_ref in ex.P7_R54_AHR_POST_CR22_EX09_ROW_BODYFREE_FALSE_FLAG_REFS)
        assert row["plan_candidate_flags"]["p8_implementation_spec_finalized_here"] is False
    _assert_bodyfree_no_touch_nonpromotion(material)
    assert ex.assert_p7_r54_ahr_post_cr22_ex09_sanitized_review_result_rows_intake_contract(material) is True


@pytest.mark.parametrize(
    ("mutator", "expected_blocker"),
    (
        (lambda rows: rows.pop(), "sanitized_selection_row_count_not_24"),
        (lambda rows: rows[0].update({"axis_scores": {"history_connection_naturalness": 1.0}}), "selection_row_axis_refs_mismatch"),
        (lambda rows: rows[0]["axis_scores"].update({"creepy_absence": 1.5}), "selection_row_axis_score_invalid"),
        (lambda rows: rows[0].update({"verdict": "MAYBE"}), "selection_row_verdict_not_allowed"),
        (lambda rows: rows[0].update({"question_need_primary_class": "question_text_needed_now"}), "selection_row_option_ref_not_allowed"),
        (lambda rows: rows[0].update({"one_question_fit_ref": "write_question_text_now"}), "selection_row_option_ref_not_allowed"),
        (lambda rows: rows[0].update({"reviewed_at_bucket_ref": ""}), "selection_row_reviewed_at_ref_missing"),
        (lambda rows: rows[0].update({"question_text_included": True}), "selection_row_bodyfree_forbidden_flag_not_false"),
        (lambda rows: rows[0].update({"row_source_ref": "unit_test_contract_rows"}), "selection_row_source_ref_forbidden"),
        (lambda rows: rows[0]["plan_candidate_flags"].update({"p8_implementation_spec_finalized_here": True}), "selection_row_p8_implementation_spec_finalized_here"),
    ),
)
def test_ex09_blocks_invalid_rows_without_echoing_body_or_promoting(mutator, expected_blocker: str) -> None:
    ex07 = _accepted_ex07()
    rows = _actual_selection_rows_input(ex07)
    ex08 = ex.build_p7_r54_ahr_post_cr22_ex08_actual_selection_row_provenance_guard(
        actual_operation_receipt_intake=ex07,
        selection_result_rows=rows,
    )
    bad_rows = deepcopy(rows)
    mutator(bad_rows)

    material = ex.build_p7_r54_ahr_post_cr22_ex09_sanitized_review_result_rows_intake(
        actual_selection_row_provenance_guard=ex08,
        selection_result_rows=bad_rows,
    )

    assert material["sanitized_review_result_rows_intake_ready"] is False
    assert expected_blocker in material["sanitized_review_result_rows_intake_blocker_refs"]
    assert material["review_result_rows"] == []
    assert material["sanitized_review_result_row_count"] == 0
    assert material["actual_sanitized_review_result_rows_intaken_here"] is False
    assert material["actual_human_review_executed_by_person"] is False
    assert material["actual_review_evidence_complete"] is False
    assert material["p8_start_allowed"] is False
    assert ex.assert_p7_r54_ahr_post_cr22_ex09_sanitized_review_result_rows_intake_contract(material) is True


def test_ex09_rejects_path_shaped_reviewed_bucket_without_echoing_path_values() -> None:
    ex07 = _accepted_ex07()
    rows = _actual_selection_rows_input(ex07)
    ex08 = ex.build_p7_r54_ahr_post_cr22_ex08_actual_selection_row_provenance_guard(
        actual_operation_receipt_intake=ex07,
        selection_result_rows=rows,
    )
    bad_rows = deepcopy(rows)
    bad_rows[0]["reviewed_at_bucket_ref"] = "../secret-reviewed-bucket"

    material = ex.build_p7_r54_ahr_post_cr22_ex09_sanitized_review_result_rows_intake(
        actual_selection_row_provenance_guard=ex08,
        selection_result_rows=bad_rows,
    )

    assert material["sanitized_review_result_rows_intake_ready"] is False
    assert "selection_row_ref_must_be_bodyfree_ref_not_path" in material["sanitized_review_result_rows_intake_blocker_refs"]
    assert "secret-reviewed-bucket" not in repr(material)
    assert ex.assert_p7_r54_ahr_post_cr22_ex09_sanitized_review_result_rows_intake_contract(material) is True


@pytest.mark.parametrize(
    ("field", "value"),
    (
        ("sanitized_review_result_rows_intake_ready", False),
        ("sanitized_selection_only_result_rows_intaken_here", False),
        ("actual_sanitized_review_result_rows_intaken_here", False),
        ("actual_human_review_executed_by_person", False),
        ("actual_selection_rows_created_here", True),
        ("actual_rating_rows_materialized_here", True),
        ("actual_question_need_observation_rows_materialized_here", True),
        ("actual_review_evidence_complete", True),
        ("question_text_materialized_here", True),
        ("p8_question_implementation_spec_finalized_here", True),
        ("p8_start_allowed", True),
        ("release_allowed", True),
        ("next_required_step", "mutated_next_step"),
    ),
)
def test_ex09_contract_rejects_evidence_question_or_promotion_mutations(field: str, value: object) -> None:
    material = deepcopy(_accepted_ex09())
    material[field] = value

    with pytest.raises(ValueError):
        ex.assert_p7_r54_ahr_post_cr22_ex09_sanitized_review_result_rows_intake_contract(material)


def test_ex08_and_ex09_alias_functions_match_primary_builders_and_contracts() -> None:
    ex07 = _accepted_ex07()
    rows = _actual_selection_rows_input(ex07)
    ex08_primary = ex.build_p7_r54_ahr_post_cr22_ex08_actual_selection_row_provenance_guard(
        actual_operation_receipt_intake=ex07,
        selection_result_rows=rows,
    )
    ex08_alias = (
        ex.build_p7_r54_ahr_post_cr22_actual_local_review_execution_evidence_completion_actual_selection_row_provenance_guard_bodyfree(
            actual_operation_receipt_intake=ex07,
            selection_result_rows=rows,
        )
    )
    assert ex08_alias == ex08_primary
    assert (
        ex.assert_p7_r54_ahr_post_cr22_actual_local_review_execution_evidence_completion_actual_selection_row_provenance_guard_bodyfree_contract(
            ex08_alias
        )
        is True
    )

    ex09_primary = ex.build_p7_r54_ahr_post_cr22_ex09_sanitized_review_result_rows_intake(
        actual_selection_row_provenance_guard=ex08_primary,
        selection_result_rows=rows,
    )
    ex09_alias = (
        ex.build_p7_r54_ahr_post_cr22_actual_local_review_execution_evidence_completion_sanitized_review_result_rows_intake_bodyfree(
            actual_selection_row_provenance_guard=ex08_primary,
            selection_result_rows=rows,
        )
    )
    assert ex09_alias == ex09_primary
    assert (
        ex.assert_p7_r54_ahr_post_cr22_actual_local_review_execution_evidence_completion_sanitized_review_result_rows_intake_bodyfree_contract(
            ex09_alias
        )
        is True
    )
