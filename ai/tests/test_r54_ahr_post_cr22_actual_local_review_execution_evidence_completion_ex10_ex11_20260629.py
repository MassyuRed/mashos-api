# -*- coding: utf-8 -*-
"""R54-AHR Post-CR22 actual local review evidence completion EX10-EX11 tests."""

from __future__ import annotations

from copy import deepcopy
from typing import Callable

import pytest

import emlis_ai_p7_r54_ahr_current_received_snapshot_actual_local_review_operation_20260628 as cr
import emlis_ai_p7_r54_ahr_post_cr22_actual_local_review_execution_evidence_completion_20260629 as ex


_FALSE_FLAG_ALLOW_EX10_EX11 = (
    "actual_rating_rows_materialized_here",
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


def _accepted_ex10(
    mutator: Callable[[list[dict[str, object]]], None] | None = None,
) -> dict[str, object]:
    return ex.build_p7_r54_ahr_post_cr22_ex10_rating_row_normalization_threshold_summary(
        sanitized_review_result_rows_intake=_accepted_ex09(mutator=mutator),
    )


def test_ex10_blocks_without_ready_ex09_and_keeps_nonpromotion_false() -> None:
    material = ex.build_p7_r54_ahr_post_cr22_ex10_rating_row_normalization_threshold_summary()

    assert set(material) == set(ex.P7_R54_AHR_POST_CR22_EX10_REQUIRED_FIELD_REFS)
    assert material["schema_version"] == ex.P7_R54_AHR_POST_CR22_EX10_RATING_ROW_NORMALIZATION_THRESHOLD_SUMMARY_SCHEMA_VERSION
    assert material["operation_step_ref"] == ex.P7_R54_AHR_POST_CR22_EX10_STEP_REF
    assert material["rating_row_normalization_ready"] is False
    assert material["rating_row_normalization_status_ref"] == ex.P7_R54_AHR_POST_CR22_EX10_RATING_ROWS_BLOCKED_STATUS_REF
    assert "ex09_sanitized_review_result_rows_not_ready" in material["rating_row_normalization_blocker_refs"]
    assert material["rating_rows"] == []
    assert material["rating_row_count"] == 0
    assert material["actual_rating_rows_materialized_here"] is False
    assert material["actual_review_evidence_complete"] is False
    assert material["next_required_step"] == ex.P7_R54_AHR_POST_CR22_EX10_DEFAULT_BLOCKED_NEXT_REQUIRED_STEP_REF
    _assert_bodyfree_no_touch_nonpromotion(material)
    assert ex.assert_p7_r54_ahr_post_cr22_ex10_rating_row_normalization_threshold_summary_contract(material) is True


def test_ex10_normalizes_24_actual_sanitized_rows_into_bodyfree_rating_rows() -> None:
    material = _accepted_ex10()

    assert set(material) == set(ex.P7_R54_AHR_POST_CR22_EX10_REQUIRED_FIELD_REFS)
    assert material["rating_row_normalization_ready"] is True
    assert material["rating_row_normalization_status_ref"] == ex.P7_R54_AHR_POST_CR22_EX10_RATING_ROWS_NORMALIZED_STATUS_REF
    assert material["rating_row_normalization_blocker_refs"] == []
    assert material["rating_row_count"] == 24
    assert material["rating_row_ref_count"] == 24
    assert material["axis_refs"] == list(cr.P7_R54_AHR_CR08_RATING_AXIS_REFS)
    assert material["axis_ref_count"] == len(cr.P7_R54_AHR_CR08_RATING_AXIS_REFS)
    assert material["axis_score_count_per_row"] == len(cr.P7_R54_AHR_CR08_RATING_AXIS_REFS)
    assert material["average_axis_scores_present"] is True
    assert material["all_axis_target_passed"] is True
    assert material["below_target_axis_ref_counts"] == {axis_ref: 0 for axis_ref in cr.P7_R54_AHR_CR08_RATING_AXIS_REFS}
    assert material["rating_rows_bodyfree_only"] is True
    assert material["rating_rows_match_sanitized_review_result_case_refs"] is True
    assert material["rating_rows_have_required_axis_scores"] is True
    assert material["rating_scores_in_range"] is True
    assert material["rating_rows_have_allowed_verdict_refs"] is True
    assert material["actual_rating_rows_materialized_here"] is True
    assert material["actual_question_need_observation_rows_materialized_here"] is False
    assert material["actual_disposal_receipt_materialized_here"] is False
    assert material["actual_review_evidence_complete"] is False
    assert material["readfeel_execution_blocker_classification_allowed_next"] is True
    assert tuple(material["implemented_steps"]) == ex.P7_R54_AHR_POST_CR22_EX10_IMPLEMENTED_STEPS
    assert tuple(material["not_yet_implemented_steps"]) == ex.P7_R54_AHR_POST_CR22_EX10_NOT_YET_IMPLEMENTED_STEPS
    assert material["next_required_step"] == ex.P7_R54_AHR_POST_CR22_EX11_STEP_REF
    for rating_row in material["rating_rows"]:
        assert set(rating_row) == set(ex.P7_R54_AHR_POST_CR22_EX10_RATING_ROW_REQUIRED_FIELD_REFS)
        assert rating_row["schema_version"] == ex.P7_R54_AHR_POST_CR22_EX10_RATING_ROW_SCHEMA_VERSION
        assert rating_row["source_actual_selection_row_provenance_verified"] is True
        assert rating_row["body_free"] is True
        assert all(rating_row[flag_ref] is False for flag_ref in ex.P7_R54_AHR_POST_CR22_EX10_ROW_BODYFREE_FALSE_FLAG_REFS)
    _assert_bodyfree_no_touch_nonpromotion(material, allowed_true_false_flags=_FALSE_FLAG_ALLOW_EX10_EX11)
    assert ex.assert_p7_r54_ahr_post_cr22_ex10_rating_row_normalization_threshold_summary_contract(material) is True


def test_ex10_records_below_target_threshold_summary_without_promoting_evidence_complete() -> None:
    def mutate(rows: list[dict[str, object]]) -> None:
        rows[0]["axis_scores"] = deepcopy(rows[0]["axis_scores"])
        rows[0]["axis_scores"]["history_connection_naturalness"] = 0.5
        rows[0]["verdict"] = "YELLOW"

    material = _accepted_ex10(mutator=mutate)

    assert material["rating_row_normalization_ready"] is True
    assert material["rating_row_count"] == 24
    assert material["all_axis_target_passed"] is False
    assert material["below_target_case_count"] == 1
    first_case_ref = material["case_ref_ids"][0]
    assert material["below_target_axis_refs_by_case"][first_case_ref] == ["history_connection_naturalness"]
    assert material["below_target_axis_ref_counts"]["history_connection_naturalness"] == 1
    assert material["yellow_case_count"] == 1
    assert material["actual_rating_rows_materialized_here"] is True
    assert material["actual_review_evidence_complete"] is False
    assert ex.assert_p7_r54_ahr_post_cr22_ex10_rating_row_normalization_threshold_summary_contract(material) is True


@pytest.mark.parametrize(
    ("field", "value"),
    (
        ("actual_review_evidence_complete", True),
        ("p8_start_allowed", True),
        ("actual_question_need_observation_rows_materialized_here", True),
        ("actual_rating_rows_materialized_here", False),
        ("next_required_step", "mutated_next_step"),
    ),
)
def test_ex10_contract_rejects_promotion_or_materialization_mutations(field: str, value: object) -> None:
    material = _accepted_ex10()
    material[field] = value

    with pytest.raises(ValueError):
        ex.assert_p7_r54_ahr_post_cr22_ex10_rating_row_normalization_threshold_summary_contract(material)


def test_ex10_alias_builders_match_primary_contract() -> None:
    material = ex.build_p7_r54_ahr_post_cr22_actual_local_review_execution_evidence_completion_rating_row_normalization_threshold_summary_bodyfree(
        sanitized_review_result_rows_intake=_accepted_ex09(),
    )

    assert material["schema_version"] == ex.P7_R54_AHR_POST_CR22_EX10_RATING_ROW_NORMALIZATION_THRESHOLD_SUMMARY_SCHEMA_VERSION
    assert material["rating_row_normalization_ready"] is True
    assert ex.assert_p7_r54_ahr_post_cr22_actual_local_review_execution_evidence_completion_rating_row_normalization_threshold_summary_bodyfree_contract(material) is True


def test_ex11_blocks_without_ready_ex10_and_keeps_nonpromotion_false() -> None:
    material = ex.build_p7_r54_ahr_post_cr22_ex11_readfeel_execution_p5_p4_blocker_classification()

    assert set(material) == set(ex.P7_R54_AHR_POST_CR22_EX11_REQUIRED_FIELD_REFS)
    assert material["schema_version"] == ex.P7_R54_AHR_POST_CR22_EX11_READFEEL_EXECUTION_P5_P4_BLOCKER_CLASSIFICATION_SCHEMA_VERSION
    assert material["operation_step_ref"] == ex.P7_R54_AHR_POST_CR22_EX11_STEP_REF
    assert material["readfeel_execution_p5_p4_blocker_classification_ready"] is False
    assert material["readfeel_execution_p5_p4_blocker_classification_status_ref"] == ex.P7_R54_AHR_POST_CR22_EX11_BLOCKERS_BLOCKED_STATUS_REF
    assert "ex10_rating_rows_not_ready" in material["readfeel_execution_p5_p4_blocker_classification_blocker_refs"]
    assert material["blocker_rows"] == []
    assert material["actual_rating_rows_materialized_here"] is False
    assert material["actual_review_evidence_complete"] is False
    assert material["next_required_step"] == ex.P7_R54_AHR_POST_CR22_EX11_DEFAULT_BLOCKED_NEXT_REQUIRED_STEP_REF
    _assert_bodyfree_no_touch_nonpromotion(material)
    assert ex.assert_p7_r54_ahr_post_cr22_ex11_readfeel_execution_p5_p4_blocker_classification_contract(material) is True


def test_ex11_classifies_clean_rating_rows_as_no_blocker_without_p8_start() -> None:
    material = ex.build_p7_r54_ahr_post_cr22_ex11_readfeel_execution_p5_p4_blocker_classification(
        rating_row_normalization_threshold_summary=_accepted_ex10(),
    )

    assert set(material) == set(ex.P7_R54_AHR_POST_CR22_EX11_REQUIRED_FIELD_REFS)
    assert material["readfeel_execution_p5_p4_blocker_classification_ready"] is True
    assert material["readfeel_execution_p5_p4_blocker_classification_status_ref"] == ex.P7_R54_AHR_POST_CR22_EX11_BLOCKERS_CLASSIFIED_STATUS_REF
    assert material["readfeel_execution_p5_p4_blocker_classification_blocker_refs"] == []
    assert material["source_rating_row_count"] == 24
    assert material["blocker_row_count"] == 0
    assert material["no_blocker_case_count"] == 24
    assert material["p5_repair_required_case_count"] == 0
    assert material["p4_current_only_repair_required_case_count"] == 0
    assert material["operation_blocked_case_count"] == 0
    assert material["inconclusive_case_count"] == 0
    assert material["p8_material_candidate_case_count_bodyfree_only"] == 0
    assert material["p5_p4_operation_blockers_not_escaped_to_p8_candidate"] is True
    assert material["actual_rating_rows_materialized_here"] is True
    assert material["actual_question_need_observation_rows_materialized_here"] is False
    assert material["actual_review_evidence_complete"] is False
    assert material["question_need_observation_normalization_allowed_next"] is True
    assert tuple(material["implemented_steps"]) == ex.P7_R54_AHR_POST_CR22_EX11_IMPLEMENTED_STEPS
    assert tuple(material["not_yet_implemented_steps"]) == ex.P7_R54_AHR_POST_CR22_EX11_NOT_YET_IMPLEMENTED_STEPS
    assert material["next_required_step"] == ex.P7_R54_AHR_POST_CR22_EX12_STEP_REF
    _assert_bodyfree_no_touch_nonpromotion(material, allowed_true_false_flags=_FALSE_FLAG_ALLOW_EX10_EX11)
    assert ex.assert_p7_r54_ahr_post_cr22_ex11_readfeel_execution_p5_p4_blocker_classification_contract(material) is True


def test_ex11_classifies_readfeel_execution_p4_below_target_and_inconclusive_blockers() -> None:
    def mutate(rows: list[dict[str, object]]) -> None:
        rows[0]["readfeel_blocker_ids"] = ["history_connection_weak"]
        rows[1]["execution_blocker_ids"] = ["question_text_leak"]
        rows[2]["repair_required_refs"] = ["p4_current_surface_repair_required"]
        rows[2]["verdict"] = "REPAIR_REQUIRED"
        rows[3]["axis_scores"] = deepcopy(rows[3]["axis_scores"])
        rows[3]["axis_scores"]["non_shallow_repeat"] = 0.1
        rows[4]["question_need_primary_class"] = "insufficient_material_execution_blocker"
        rows[4]["one_question_fit_ref"] = "insufficient_material"
        rows[4]["verdict"] = "NOT_REVIEWABLE"
        rows[5]["verdict"] = "RED"

    material = ex.build_p7_r54_ahr_post_cr22_ex11_readfeel_execution_p5_p4_blocker_classification(
        rating_row_normalization_threshold_summary=_accepted_ex10(mutator=mutate),
    )

    assert material["readfeel_execution_p5_p4_blocker_classification_ready"] is True
    assert material["blocker_row_count"] >= 5
    assert material["readfeel_blocker_row_count"] >= 1
    assert material["execution_blocker_row_count"] == 1
    assert material["repair_required_blocker_row_count"] >= 1
    assert material["below_target_axis_blocker_row_count"] == 1
    assert material["inconclusive_blocker_row_count"] == 1
    assert material["verdict_blocker_row_count"] >= 1
    assert material["blocker_category_counts"]["p5_history_connection_weak"] >= 1
    assert material["blocker_category_counts"]["operation_blocked_question_text"] == 1
    assert material["blocker_category_counts"]["p4_current_only_surface_repair_required"] >= 1
    assert material["blocker_category_counts"]["p5_readfeel_repair_required"] >= 1
    assert material["blocker_category_counts"]["inconclusive_insufficient_material"] >= 1
    assert material["p8_material_candidate_case_count_bodyfree_only"] == 0
    assert material["p5_p4_operation_blockers_not_escaped_to_p8_candidate"] is True
    for blocker_row in material["blocker_rows"]:
        assert set(blocker_row) == set(ex.P7_R54_AHR_POST_CR22_EX11_BLOCKER_ROW_REQUIRED_FIELD_REFS)
        assert blocker_row["schema_version"] == ex.P7_R54_AHR_POST_CR22_EX11_BLOCKER_ROW_SCHEMA_VERSION
        assert blocker_row["body_free"] is True
        assert all(blocker_row[flag_ref] is False for flag_ref in ex.P7_R54_AHR_POST_CR22_EX11_BLOCKER_ROW_BODYFREE_FALSE_FLAG_REFS)
    assert ex.assert_p7_r54_ahr_post_cr22_ex11_readfeel_execution_p5_p4_blocker_classification_contract(material) is True


def test_ex11_keeps_clean_p8_candidate_bodyfree_only_and_not_started() -> None:
    def mutate(rows: list[dict[str, object]]) -> None:
        rows[0]["question_need_primary_class"] = "question_may_reduce_overread_risk"
        rows[0]["one_question_fit_ref"] = "fits_one_question"
        rows[0]["plan_candidate_flags"] = dict(rows[0]["plan_candidate_flags"])
        rows[0]["plan_candidate_flags"]["p8_design_material_candidate"] = True
        rows[0]["plan_candidate_flags"]["plus_single_question_candidate_later"] = True
        rows[0]["sanitized_reason_ids"] = ["question_may_reduce_overread_risk_later"]

    material = ex.build_p7_r54_ahr_post_cr22_ex11_readfeel_execution_p5_p4_blocker_classification(
        rating_row_normalization_threshold_summary=_accepted_ex10(mutator=mutate),
    )

    assert material["readfeel_execution_p5_p4_blocker_classification_ready"] is True
    assert material["blocker_row_count"] == 0
    assert material["p8_material_candidate_case_count_bodyfree_only"] == 1
    assert material["p8_material_candidate_blocked_by_blocker_case_count"] == 0
    assert material["p8_start_allowed"] is False
    assert material["p8_question_implementation_started"] is False
    assert material["actual_review_evidence_complete"] is False
    assert ex.assert_p7_r54_ahr_post_cr22_ex11_readfeel_execution_p5_p4_blocker_classification_contract(material) is True


@pytest.mark.parametrize(
    ("field", "value"),
    (
        ("actual_review_evidence_complete", True),
        ("p8_start_allowed", True),
        ("actual_question_need_observation_rows_materialized_here", True),
        ("actual_rating_rows_materialized_here", False),
        ("next_required_step", "mutated_next_step"),
    ),
)
def test_ex11_contract_rejects_promotion_or_materialization_mutations(field: str, value: object) -> None:
    material = ex.build_p7_r54_ahr_post_cr22_ex11_readfeel_execution_p5_p4_blocker_classification(
        rating_row_normalization_threshold_summary=_accepted_ex10(),
    )
    material[field] = value

    with pytest.raises(ValueError):
        ex.assert_p7_r54_ahr_post_cr22_ex11_readfeel_execution_p5_p4_blocker_classification_contract(material)


def test_ex11_alias_builders_match_primary_contract() -> None:
    material = ex.build_p7_r54_ahr_post_cr22_actual_local_review_execution_evidence_completion_readfeel_execution_p5_p4_blocker_classification_bodyfree(
        rating_row_normalization_threshold_summary=_accepted_ex10(),
    )

    assert material["schema_version"] == ex.P7_R54_AHR_POST_CR22_EX11_READFEEL_EXECUTION_P5_P4_BLOCKER_CLASSIFICATION_SCHEMA_VERSION
    assert material["readfeel_execution_p5_p4_blocker_classification_ready"] is True
    assert ex.assert_p7_r54_ahr_post_cr22_actual_local_review_execution_evidence_completion_readfeel_execution_p5_p4_blocker_classification_bodyfree_contract(material) is True
