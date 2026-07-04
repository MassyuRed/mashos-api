# -*- coding: utf-8 -*-
"""R54-AHR Post-CR22 actual local review evidence completion EX12-EX13 tests."""

from __future__ import annotations

from copy import deepcopy
from typing import Callable

import pytest

import emlis_ai_p7_r54_ahr_current_received_snapshot_actual_local_review_operation_20260628 as cr
import emlis_ai_p7_r54_ahr_post_cr22_actual_local_review_execution_evidence_completion_20260629 as ex


_FALSE_FLAG_ALLOW_EX12_EX13 = (
    "actual_rating_rows_materialized_here",
    "actual_question_need_observation_rows_materialized_here",
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


def _accepted_ex10_and_sources(
    mutator: Callable[[list[dict[str, object]]], None] | None = None,
) -> tuple[dict[str, object], dict[str, object]]:
    ex09 = _accepted_ex09(mutator=mutator)
    ex10 = ex.build_p7_r54_ahr_post_cr22_ex10_rating_row_normalization_threshold_summary(
        sanitized_review_result_rows_intake=ex09,
    )
    return ex09, ex10


def _accepted_ex11(
    mutator: Callable[[list[dict[str, object]]], None] | None = None,
) -> dict[str, object]:
    return ex.build_p7_r54_ahr_post_cr22_ex11_readfeel_execution_p5_p4_blocker_classification(
        rating_row_normalization_threshold_summary=_accepted_ex10(mutator=mutator),
    )


def _accepted_ex09_ex10_ex11(
    mutator: Callable[[list[dict[str, object]]], None] | None = None,
) -> tuple[dict[str, object], dict[str, object], dict[str, object]]:
    ex09, ex10 = _accepted_ex10_and_sources(mutator=mutator)
    ex11 = ex.build_p7_r54_ahr_post_cr22_ex11_readfeel_execution_p5_p4_blocker_classification(
        rating_row_normalization_threshold_summary=ex10,
    )
    return ex09, ex10, ex11


def _accepted_ex12(
    mutator: Callable[[list[dict[str, object]]], None] | None = None,
) -> dict[str, object]:
    ex09, ex10, ex11 = _accepted_ex09_ex10_ex11(mutator=mutator)
    return ex.build_p7_r54_ahr_post_cr22_ex12_question_need_observation_normalization(
        sanitized_review_result_rows_intake=ex09,
        rating_row_normalization_threshold_summary=ex10,
        readfeel_execution_p5_p4_blocker_classification=ex11,
    )


def _accepted_ex10_ex11_ex12(
    mutator: Callable[[list[dict[str, object]]], None] | None = None,
) -> tuple[dict[str, object], dict[str, object], dict[str, object]]:
    ex09, ex10, ex11 = _accepted_ex09_ex10_ex11(mutator=mutator)
    ex12 = ex.build_p7_r54_ahr_post_cr22_ex12_question_need_observation_normalization(
        sanitized_review_result_rows_intake=ex09,
        rating_row_normalization_threshold_summary=ex10,
        readfeel_execution_p5_p4_blocker_classification=ex11,
    )
    return ex10, ex11, ex12


def _mutate_first_row_to_clean_p8_candidate(rows: list[dict[str, object]]) -> None:
    rows[0]["question_need_primary_class"] = "question_may_reduce_overread_risk"
    rows[0]["one_question_fit_ref"] = "fits_one_question"
    rows[0]["plan_candidate_flags"] = dict(rows[0]["plan_candidate_flags"])
    rows[0]["plan_candidate_flags"]["p8_design_material_candidate"] = True
    rows[0]["plan_candidate_flags"]["plus_single_question_candidate_later"] = True
    rows[0]["sanitized_reason_ids"] = ["question_may_reduce_overread_risk_later"]


def test_ex12_blocks_without_ready_sources_and_keeps_nonpromotion_false() -> None:
    material = ex.build_p7_r54_ahr_post_cr22_ex12_question_need_observation_normalization()

    assert set(material) == set(ex.P7_R54_AHR_POST_CR22_EX12_REQUIRED_FIELD_REFS)
    assert material["schema_version"] == ex.P7_R54_AHR_POST_CR22_EX12_QUESTION_NEED_OBSERVATION_NORMALIZATION_SCHEMA_VERSION
    assert material["operation_step_ref"] == ex.P7_R54_AHR_POST_CR22_EX12_STEP_REF
    assert material["question_need_observation_normalization_ready"] is False
    assert material["question_need_observation_normalization_status_ref"] == ex.P7_R54_AHR_POST_CR22_EX12_QUESTION_OBSERVATIONS_BLOCKED_STATUS_REF
    assert "ex09_sanitized_review_result_rows_not_ready" in material["question_need_observation_normalization_step_blocker_refs"]
    assert "ex10_rating_rows_not_ready" in material["question_need_observation_normalization_step_blocker_refs"]
    assert "ex11_blocker_classification_not_ready" in material["question_need_observation_normalization_step_blocker_refs"]
    assert material["question_need_observation_rows"] == []
    assert material["question_need_observation_row_count"] == 0
    assert material["actual_question_need_observation_rows_materialized_here"] is False
    assert material["actual_review_evidence_complete"] is False
    assert material["p8_start_allowed"] is False
    assert material["next_required_step"] == ex.P7_R54_AHR_POST_CR22_EX12_DEFAULT_BLOCKED_NEXT_REQUIRED_STEP_REF
    _assert_bodyfree_no_touch_nonpromotion(material)
    assert ex.assert_p7_r54_ahr_post_cr22_ex12_question_need_observation_normalization_contract(material) is True


def test_ex12_normalizes_24_question_need_observation_rows_without_question_text_or_p8_start() -> None:
    material = _accepted_ex12()

    assert set(material) == set(ex.P7_R54_AHR_POST_CR22_EX12_REQUIRED_FIELD_REFS)
    assert material["question_need_observation_normalization_ready"] is True
    assert material["question_need_observation_normalization_status_ref"] == ex.P7_R54_AHR_POST_CR22_EX12_QUESTION_OBSERVATIONS_NORMALIZED_STATUS_REF
    assert material["question_need_observation_normalization_step_blocker_refs"] == []
    assert material["question_need_observation_row_count"] == 24
    assert material["question_need_observation_row_ref_count"] == 24
    assert material["case_ref_id_count"] == 24
    assert material["case_ref_ids_unique"] is True
    assert material["question_need_observation_rows_normalized_here"] is True
    assert material["actual_question_need_observation_rows_materialized_here"] is True
    assert material["actual_rating_rows_materialized_here"] is True
    assert material["rows_bodyfree_only"] is True
    assert material["rows_have_no_question_text"] is True
    assert material["question_text_materialized_here"] is False
    assert material["draft_question_text_materialized_here"] is False
    assert material["p8_question_implementation_spec_finalized_here"] is False
    assert material["p8_start_allowed"] is False
    assert material["actual_review_evidence_complete"] is False
    assert tuple(material["implemented_steps"]) == ex.P7_R54_AHR_POST_CR22_EX12_IMPLEMENTED_STEPS
    assert tuple(material["not_yet_implemented_steps"]) == ex.P7_R54_AHR_POST_CR22_EX12_NOT_YET_IMPLEMENTED_STEPS
    assert material["next_required_step"] == ex.P7_R54_AHR_POST_CR22_EX13_STEP_REF
    for row in material["question_need_observation_rows"]:
        assert set(row) == set(ex.P7_R54_AHR_POST_CR22_EX12_QUESTION_NEED_OBSERVATION_ROW_REQUIRED_FIELD_REFS)
        assert row["schema_version"] == ex.P7_R54_AHR_POST_CR22_EX12_QUESTION_NEED_OBSERVATION_ROW_SCHEMA_VERSION
        assert row["body_free"] is True
        assert row["question_text_materialized_here"] is False
        assert row["draft_question_text_materialized_here"] is False
        assert row["p8_implementation_spec_finalized_here"] is False
        assert row["p8_start_allowed"] is False
        assert all(row[flag_ref] is False for flag_ref in ex.P7_R54_AHR_POST_CR22_EX12_QUESTION_OBSERVATION_ROW_BODYFREE_FALSE_FLAG_REFS)
    _assert_bodyfree_no_touch_nonpromotion(material, allowed_true_false_flags=_FALSE_FLAG_ALLOW_EX12_EX13)
    assert ex.assert_p7_r54_ahr_post_cr22_ex12_question_need_observation_normalization_contract(material) is True


def test_ex12_keeps_clean_p8_candidate_bodyfree_only_without_question_text_or_start() -> None:
    material = _accepted_ex12(mutator=_mutate_first_row_to_clean_p8_candidate)

    assert material["question_need_observation_normalization_ready"] is True
    assert material["p8_material_candidate_case_count_bodyfree_only"] == 1
    assert material["plus_single_question_candidate_case_count"] == 0
    assert material["premium_deep_dive_candidate_case_count"] == 0
    assert material["question_may_reduce_overread_risk_case_count"] == 1
    assert material["question_text_materialized_here"] is False
    assert material["draft_question_text_materialized_here"] is False
    assert material["p8_start_allowed"] is False
    first_row = material["question_need_observation_rows"][0]
    assert first_row["p8_design_material_candidate"] is True
    assert first_row["p8_material_candidate_reason_ref"] == "p8_material_candidate_bodyfree_only"
    assert first_row["question_text_materialized_here"] is False
    assert first_row["p8_start_allowed"] is False
    assert ex.assert_p7_r54_ahr_post_cr22_ex12_question_need_observation_normalization_contract(material) is True


def test_ex12_prevents_p5_p4_operation_or_readfeel_blockers_from_becoming_p8_material() -> None:
    def mutate(rows: list[dict[str, object]]) -> None:
        _mutate_first_row_to_clean_p8_candidate(rows)
        rows[0]["readfeel_blocker_ids"] = ["history_connection_weak"]
        rows[1]["question_need_primary_class"] = "plus_single_question_candidate_later"
        rows[1]["one_question_fit_ref"] = "fits_one_question"
        rows[1]["plan_candidate_flags"] = dict(rows[1]["plan_candidate_flags"])
        rows[1]["plan_candidate_flags"]["p8_design_material_candidate"] = True
        rows[1]["repair_required_refs"] = ["p4_current_surface_repair_required"]
        rows[2]["question_need_primary_class"] = "premium_deep_dive_candidate_later"
        rows[2]["one_question_fit_ref"] = "fits_one_question"
        rows[2]["plan_candidate_flags"] = dict(rows[2]["plan_candidate_flags"])
        rows[2]["plan_candidate_flags"]["p8_design_material_candidate"] = True
        rows[2]["execution_blocker_ids"] = ["packet_missing"]

    material = _accepted_ex12(mutator=mutate)

    assert material["question_need_observation_normalization_ready"] is True
    assert material["question_need_observation_row_count"] == 24
    assert material["p8_material_candidate_case_count_bodyfree_only"] == 0
    assert material["p5_repair_required_case_count"] >= 1
    assert material["p4_current_surface_repair_required_case_count"] >= 1
    assert material["operation_blocker_case_count"] >= 1
    assert material["readfeel_blocker_case_count"] >= 1
    assert all(row["p8_design_material_candidate"] is False for row in material["question_need_observation_rows"][:3])
    assert material["p8_start_allowed"] is False
    assert ex.assert_p7_r54_ahr_post_cr22_ex12_question_need_observation_normalization_contract(material) is True


@pytest.mark.parametrize(
    ("field", "value"),
    (
        ("actual_review_evidence_complete", True),
        ("p8_start_allowed", True),
        ("question_text_materialized_here", True),
        ("draft_question_text_materialized_here", True),
        ("actual_question_need_observation_rows_materialized_here", False),
        ("next_required_step", "mutated_next_step"),
    ),
)
def test_ex12_contract_rejects_promotion_question_text_or_materialization_mutations(field: str, value: object) -> None:
    material = _accepted_ex12()
    material[field] = value

    with pytest.raises(ValueError):
        ex.assert_p7_r54_ahr_post_cr22_ex12_question_need_observation_normalization_contract(material)


def test_ex12_contract_rejects_question_row_text_or_p8_start_mutations() -> None:
    material = _accepted_ex12()
    material["question_need_observation_rows"] = deepcopy(material["question_need_observation_rows"])
    material["question_need_observation_rows"][0]["question_text_materialized_here"] = True

    with pytest.raises(ValueError):
        ex.assert_p7_r54_ahr_post_cr22_ex12_question_need_observation_normalization_contract(material)


def test_ex12_alias_builders_match_primary_contract() -> None:
    ex09, ex10, ex11 = _accepted_ex09_ex10_ex11()
    material = ex.build_p7_r54_ahr_post_cr22_actual_local_review_execution_evidence_completion_question_need_observation_normalization_bodyfree(
        sanitized_review_result_rows_intake=ex09,
        rating_row_normalization_threshold_summary=ex10,
        readfeel_execution_p5_p4_blocker_classification=ex11,
    )

    assert material["schema_version"] == ex.P7_R54_AHR_POST_CR22_EX12_QUESTION_NEED_OBSERVATION_NORMALIZATION_SCHEMA_VERSION
    assert material["question_need_observation_normalization_ready"] is True
    assert ex.assert_p7_r54_ahr_post_cr22_actual_local_review_execution_evidence_completion_question_need_observation_normalization_bodyfree_contract(material) is True


def test_ex13_blocks_without_ready_ex12_and_keeps_nonpromotion_false() -> None:
    material = ex.build_p7_r54_ahr_post_cr22_ex13_rating_question_consistency_guard()

    assert set(material) == set(ex.P7_R54_AHR_POST_CR22_EX13_REQUIRED_FIELD_REFS)
    assert material["schema_version"] == ex.P7_R54_AHR_POST_CR22_EX13_RATING_QUESTION_CONSISTENCY_GUARD_SCHEMA_VERSION
    assert material["operation_step_ref"] == ex.P7_R54_AHR_POST_CR22_EX13_STEP_REF
    assert material["rating_question_consistency_guard_evaluated"] is False
    assert material["rating_question_consistency_guard_passed"] is False
    assert material["rating_question_consistency_guard_status_ref"] == ex.P7_R54_AHR_POST_CR22_EX13_GUARD_BLOCKED_STATUS_REF
    assert "ex12_question_observation_not_ready" in material["rating_question_consistency_guard_step_blocker_refs"]
    assert material["consistency_issue_rows"] == []
    assert material["actual_question_need_observation_rows_materialized_here"] is False
    assert material["actual_review_evidence_complete"] is False
    assert material["p8_start_allowed"] is False
    assert material["next_required_step"] == ex.P7_R54_AHR_POST_CR22_EX13_DEFAULT_BLOCKED_NEXT_REQUIRED_STEP_REF
    _assert_bodyfree_no_touch_nonpromotion(material)
    assert ex.assert_p7_r54_ahr_post_cr22_ex13_rating_question_consistency_guard_contract(material) is True


def test_ex13_passes_clean_question_rows_and_points_to_ex14_without_completing_evidence() -> None:
    ex10, ex11, ex12 = _accepted_ex10_ex11_ex12(mutator=_mutate_first_row_to_clean_p8_candidate)
    material = ex.build_p7_r54_ahr_post_cr22_ex13_rating_question_consistency_guard(
        rating_row_normalization_threshold_summary=ex10,
        readfeel_execution_p5_p4_blocker_classification=ex11,
        question_need_observation_normalization=ex12,
    )

    assert set(material) == set(ex.P7_R54_AHR_POST_CR22_EX13_REQUIRED_FIELD_REFS)
    assert material["rating_question_consistency_guard_evaluated"] is True
    assert material["rating_question_consistency_guard_passed"] is True
    assert material["rating_question_consistency_guard_status_ref"] == ex.P7_R54_AHR_POST_CR22_EX13_GUARD_PASSED_STATUS_REF
    assert material["rating_question_consistency_guard_reason_refs"] == [ex.P7_R54_AHR_POST_CR22_EX13_READY_REASON_REF]
    assert material["consistency_issue_row_count"] == 0
    assert material["consistency_issue_rows"] == []
    assert material["p8_material_candidate_case_count_bodyfree_only"] == 1
    assert material["rating_below_target_cannot_escape_to_p8_material"] is True
    assert material["creepy_or_overclaim_risk_cannot_escape_to_question_candidate"] is True
    assert material["self_blame_risk_cannot_escape_to_question_candidate"] is True
    assert material["immediate_observation_heavy_cannot_escape_to_p8_material"] is True
    assert material["insufficient_material_cannot_escape_to_p8_material"] is True
    assert material["repair_or_blocker_rows_cannot_escape_to_p8_material"] is True
    assert material["actual_question_need_observation_rows_materialized_here"] is True
    assert material["actual_rating_rows_materialized_here"] is True
    assert material["actual_review_evidence_complete"] is False
    assert material["actual_disposal_receipt_materialized_here"] is False
    assert material["p8_start_allowed"] is False
    assert tuple(material["implemented_steps"]) == ex.P7_R54_AHR_POST_CR22_EX13_IMPLEMENTED_STEPS
    assert tuple(material["not_yet_implemented_steps"]) == ex.P7_R54_AHR_POST_CR22_EX13_NOT_YET_IMPLEMENTED_STEPS
    assert material["next_required_step"] == ex.P7_R54_AHR_POST_CR22_EX14_STEP_REF
    _assert_bodyfree_no_touch_nonpromotion(material, allowed_true_false_flags=_FALSE_FLAG_ALLOW_EX12_EX13)
    assert ex.assert_p7_r54_ahr_post_cr22_ex13_rating_question_consistency_guard_contract(material) is True


def test_ex13_fails_when_p8_candidate_escapes_below_target_rating() -> None:
    ex10, ex11, ex12 = _accepted_ex10_ex11_ex12(mutator=_mutate_first_row_to_clean_p8_candidate)
    ex10 = deepcopy(ex10)
    ex10["rating_rows"] = deepcopy(ex10["rating_rows"])
    ex10["rating_rows"][0]["below_target_axis_refs"] = ["creepy_absence"]
    ex10["rating_rows"][0]["below_target_axis_ref_count"] = 1

    material = ex.build_p7_r54_ahr_post_cr22_ex13_rating_question_consistency_guard(
        rating_row_normalization_threshold_summary=ex10,
        readfeel_execution_p5_p4_blocker_classification=ex11,
        question_need_observation_normalization=ex12,
    )

    assert material["rating_question_consistency_guard_evaluated"] is True
    assert material["rating_question_consistency_guard_passed"] is False
    assert material["rating_question_consistency_guard_status_ref"] == ex.P7_R54_AHR_POST_CR22_EX13_GUARD_FAILED_STATUS_REF
    assert material["rating_question_consistency_guard_reason_refs"] == [ex.P7_R54_AHR_POST_CR22_EX13_FAILED_REASON_REF]
    assert material["consistency_issue_row_count"] >= 2
    assert material["rating_below_target_p8_escape_case_count"] == 1
    assert material["risk_axis_p8_escape_case_count"] == 1
    assert material["rating_below_target_cannot_escape_to_p8_material"] is False
    assert material["creepy_or_overclaim_risk_cannot_escape_to_question_candidate"] is False
    assert material["actual_review_evidence_complete"] is False
    assert material["next_required_step"] == ex.P7_R54_AHR_POST_CR22_EX13_DEFAULT_BLOCKED_NEXT_REQUIRED_STEP_REF
    for issue_row in material["consistency_issue_rows"]:
        assert set(issue_row) == set(ex.P7_R54_AHR_POST_CR22_EX13_CONSISTENCY_ISSUE_ROW_REQUIRED_FIELD_REFS)
        assert issue_row["schema_version"] == ex.P7_R54_AHR_POST_CR22_EX13_CONSISTENCY_ISSUE_ROW_SCHEMA_VERSION
        assert issue_row["body_free"] is True
        assert issue_row["rating_question_consistency_guard_blocks_evidence_complete"] is True
        assert issue_row["p8_material_candidate_blocked"] is True
        assert all(issue_row[flag_ref] is False for flag_ref in ex.P7_R54_AHR_POST_CR22_EX13_CONSISTENCY_ISSUE_ROW_BODYFREE_FALSE_FLAG_REFS)
    assert ex.assert_p7_r54_ahr_post_cr22_ex13_rating_question_consistency_guard_contract(material) is True


@pytest.mark.parametrize(
    ("field", "value"),
    (
        ("actual_review_evidence_complete", True),
        ("p8_start_allowed", True),
        ("question_text_materialized_here", True),
        ("draft_question_text_materialized_here", True),
        ("actual_question_need_observation_rows_materialized_here", False),
        ("next_required_step", "mutated_next_step"),
    ),
)
def test_ex13_contract_rejects_promotion_question_text_or_materialization_mutations(field: str, value: object) -> None:
    ex10, ex11, ex12 = _accepted_ex10_ex11_ex12(mutator=_mutate_first_row_to_clean_p8_candidate)
    material = ex.build_p7_r54_ahr_post_cr22_ex13_rating_question_consistency_guard(
        rating_row_normalization_threshold_summary=ex10,
        readfeel_execution_p5_p4_blocker_classification=ex11,
        question_need_observation_normalization=ex12,
    )
    material[field] = value

    with pytest.raises(ValueError):
        ex.assert_p7_r54_ahr_post_cr22_ex13_rating_question_consistency_guard_contract(material)


def test_ex13_alias_builders_match_primary_contract() -> None:
    ex10, ex11, ex12 = _accepted_ex10_ex11_ex12()
    material = ex.build_p7_r54_ahr_post_cr22_actual_local_review_execution_evidence_completion_rating_question_consistency_guard_bodyfree(
        rating_row_normalization_threshold_summary=ex10,
        readfeel_execution_p5_p4_blocker_classification=ex11,
        question_need_observation_normalization=ex12,
    )

    assert material["schema_version"] == ex.P7_R54_AHR_POST_CR22_EX13_RATING_QUESTION_CONSISTENCY_GUARD_SCHEMA_VERSION
    assert material["rating_question_consistency_guard_passed"] is True
    assert ex.assert_p7_r54_ahr_post_cr22_actual_local_review_execution_evidence_completion_rating_question_consistency_guard_bodyfree_contract(material) is True
