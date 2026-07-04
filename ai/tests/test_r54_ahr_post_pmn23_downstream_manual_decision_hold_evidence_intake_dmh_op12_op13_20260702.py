# -*- coding: utf-8 -*-
"""R54-AHR Post-PMN23 downstream manual decision hold DMH-OP12/OP13 tests."""

from __future__ import annotations

from copy import deepcopy
from pathlib import Path
import sys

import pytest

TEST_DIR = Path(__file__).resolve().parent
if str(TEST_DIR) not in sys.path:
    sys.path.insert(0, str(TEST_DIR))

import emlis_ai_p7_r54_ahr_post_pmn23_downstream_manual_decision_hold_evidence_intake_20260701 as dmh
import test_r54_ahr_post_pmn23_downstream_manual_decision_hold_evidence_intake_dmh_op10_op11_20260702 as dmh_op10_op11_prev

_READY_OP10_CACHE: dict[str, object] | None = None
_READY_OP11_CACHE: dict[str, object] | None = None
_READY_OP12_CACHE: dict[str, object] | None = None
_READY_OP13_CACHE: dict[str, object] | None = None


def _ready_op10() -> dict[str, object]:
    global _READY_OP10_CACHE
    if _READY_OP10_CACHE is None:
        material = dmh_op10_op11_prev._ready_op10()
        assert dmh.assert_p7_r54_ahr_post_pmn23_dmh_op10_sanitized_review_result_rows_intake_provenance_guard_contract(material) is True
        _READY_OP10_CACHE = material
    return deepcopy(_READY_OP10_CACHE)


def _ready_op11() -> dict[str, object]:
    global _READY_OP11_CACHE
    if _READY_OP11_CACHE is None:
        material = dmh_op10_op11_prev._ready_op11()
        assert dmh.assert_p7_r54_ahr_post_pmn23_dmh_op11_rating_rows_normalization_threshold_summary_contract(material) is True
        _READY_OP11_CACHE = material
    return deepcopy(_READY_OP11_CACHE)


def _ready_op12() -> dict[str, object]:
    global _READY_OP12_CACHE
    if _READY_OP12_CACHE is None:
        material = dmh.build_p7_r54_ahr_post_pmn23_dmh_op12_question_need_observation_rows_normalization(
            rating_rows_normalization_threshold_summary=_ready_op11(),
            sanitized_review_result_rows_intake=_ready_op10(),
        )
        assert dmh.assert_p7_r54_ahr_post_pmn23_dmh_op12_question_need_observation_rows_normalization_contract(material) is True
        _READY_OP12_CACHE = material
    return deepcopy(_READY_OP12_CACHE)


def _ready_op13() -> dict[str, object]:
    global _READY_OP13_CACHE
    if _READY_OP13_CACHE is None:
        material = dmh.build_p7_r54_ahr_post_pmn23_dmh_op13_rating_question_consistency_blocker_separation(
            question_need_observation_rows_normalization=_ready_op12(),
            rating_rows_normalization_threshold_summary=_ready_op11(),
        )
        assert dmh.assert_p7_r54_ahr_post_pmn23_dmh_op13_rating_question_consistency_blocker_separation_contract(material) is True
        _READY_OP13_CACHE = material
    return deepcopy(_READY_OP13_CACHE)


def _assert_bodyfree_no_touch_no_promotion(material: dict[str, object]) -> None:
    assert material["body_free"] is True
    for key in dmh.P7_R54_AHR_POST_PMN23_DMH_REQUIRED_FALSE_FLAG_REFS:
        assert material[key] is False, key
    for marker_map_key in ("public_contract", "post_pmn23_no_touch_contract", "body_free_markers"):
        assert material[marker_map_key]
        assert all(value is False for value in material[marker_map_key].values()), marker_map_key
    assert all(value is False for value in material["not_claimed_boundary"].values())
    for forbidden_key in dmh.P7_R54_AHR_POST_PMN23_DMH_FORBIDDEN_PAYLOAD_KEY_REFS:
        assert forbidden_key not in material, forbidden_key


def _op10_op11_with_mutated_source_row(mutator) -> tuple[dict[str, object], dict[str, object]]:
    op09 = dmh_op10_op11_prev._ready_op09()
    rows = dmh.build_p7_r54_ahr_post_pmn23_dmh_op10_sanitized_review_result_rows_bodyfree(
        review_session_id=op09["review_session_id"],
        operation_receipt_ref=op09["operation_receipt_ref"],
        reviewer_person_ref=op09["reviewer_person_ref"],
    )
    mutator(rows[0])
    op10 = dmh.build_p7_r54_ahr_post_pmn23_dmh_op10_sanitized_review_result_rows_intake_provenance_guard(
        actual_operation_receipt_intake=op09,
        sanitized_review_result_rows_bodyfree=rows,
    )
    assert dmh.assert_p7_r54_ahr_post_pmn23_dmh_op10_sanitized_review_result_rows_intake_provenance_guard_contract(op10) is True
    op11 = dmh.build_p7_r54_ahr_post_pmn23_dmh_op11_rating_rows_normalization_threshold_summary(
        sanitized_review_result_rows_intake=op10,
    )
    assert dmh.assert_p7_r54_ahr_post_pmn23_dmh_op11_rating_rows_normalization_threshold_summary_contract(op11) is True
    return op10, op11


def _op10_op11_with_low_score_and_p8_candidate() -> tuple[dict[str, object], dict[str, object]]:
    op09 = dmh_op10_op11_prev._ready_op09()
    axis = dmh.P7_R54_AHR_POST_PMN23_DMH_OP07_RATING_AXIS_REFS[0]
    rows = dmh.build_p7_r54_ahr_post_pmn23_dmh_op10_sanitized_review_result_rows_bodyfree(
        review_session_id=op09["review_session_id"],
        operation_receipt_ref=op09["operation_receipt_ref"],
        reviewer_person_ref=op09["reviewer_person_ref"],
        score_overrides_by_index={1: {axis: 0.4}},
    )
    rows[0]["question_need_primary_class_ref"] = "plus_single_question_candidate_later"
    rows[0]["one_question_fit_ref"] = "fits_one_question"
    rows[0]["plan_candidate_flags"]["plus_single_question_candidate_later"] = True
    op10 = dmh.build_p7_r54_ahr_post_pmn23_dmh_op10_sanitized_review_result_rows_intake_provenance_guard(
        actual_operation_receipt_intake=op09,
        sanitized_review_result_rows_bodyfree=rows,
    )
    assert dmh.assert_p7_r54_ahr_post_pmn23_dmh_op10_sanitized_review_result_rows_intake_provenance_guard_contract(op10) is True
    op11 = dmh.build_p7_r54_ahr_post_pmn23_dmh_op11_rating_rows_normalization_threshold_summary(
        sanitized_review_result_rows_intake=op10,
    )
    assert dmh.assert_p7_r54_ahr_post_pmn23_dmh_op11_rating_rows_normalization_threshold_summary_contract(op11) is True
    return op10, op11


def _op12_op13_from(op10: dict[str, object], op11: dict[str, object]) -> tuple[dict[str, object], dict[str, object]]:
    op12 = dmh.build_p7_r54_ahr_post_pmn23_dmh_op12_question_need_observation_rows_normalization(
        rating_rows_normalization_threshold_summary=op11,
        sanitized_review_result_rows_intake=op10,
    )
    assert dmh.assert_p7_r54_ahr_post_pmn23_dmh_op12_question_need_observation_rows_normalization_contract(op12) is True
    op13 = dmh.build_p7_r54_ahr_post_pmn23_dmh_op13_rating_question_consistency_blocker_separation(
        question_need_observation_rows_normalization=op12,
        rating_rows_normalization_threshold_summary=op11,
    )
    assert dmh.assert_p7_r54_ahr_post_pmn23_dmh_op13_rating_question_consistency_blocker_separation_contract(op13) is True
    return op12, op13


def test_dmh_op12_normalizes_24_question_need_observation_rows_without_question_text_or_p8_start() -> None:
    material = _ready_op12()

    assert set(material) == set(dmh.P7_R54_AHR_POST_PMN23_DMH_OP12_REQUIRED_FIELD_REFS)
    assert material["schema_version"] == dmh.P7_R54_AHR_POST_PMN23_DMH_OP12_QUESTION_NEED_OBSERVATION_ROWS_NORMALIZATION_SCHEMA_VERSION
    assert material["operation_step_ref"] == dmh.P7_R54_AHR_POST_PMN23_DMH_OP12_STEP_REF
    assert material["dmh_op12_status_ref"] == dmh.P7_R54_AHR_POST_PMN23_DMH_OP12_READY_STATUS_REF
    assert material["dmh_op12_ready"] is True
    assert tuple(material["dmh_op12_reason_refs"]) == dmh.P7_R54_AHR_POST_PMN23_DMH_OP12_READY_REASON_REFS
    assert material["op11_dmh_ready"] is True
    assert material["op11_next_required_step"] == dmh.P7_R54_AHR_POST_PMN23_DMH_OP12_STEP_REF
    assert material["op10_dmh_ready"] is True
    assert material["question_need_observation_row_count"] == 24
    assert material["question_need_observation_row_count_is_24"] is True
    assert material["source_sanitized_review_result_row_count"] == 24
    assert material["source_rating_row_count"] == 24
    assert material["case_ref_ids_unique"] is True
    assert material["blind_case_ids_unique"] is True
    assert material["packet_ref_ids_unique"] is True
    assert material["question_need_primary_class_counts"] == {"no_question_needed_emlis_can_observe": 24}
    assert material["one_question_fit_counts"] == {"not_needed": 24}
    assert material["p8_material_candidate_case_count_bodyfree_only"] == 0
    assert material["question_text_materialized_here"] is False
    assert material["draft_question_text_materialized_here"] is False
    assert material["question_trigger_logic_materialized_here"] is False
    assert material["question_answer_storage_materialized_here"] is False
    assert material["p8_implementation_spec_finalized_here"] is False
    assert material["p8_start_allowed"] is False
    assert material["question_need_observation_rows_normalized_here"] is True
    assert material["actual_question_need_observation_rows_materialized_from_actual_rows"] is True
    assert material["actual_question_need_observation_rows_materialized_here"] is False
    assert material["rating_question_consistency_blocker_separation_allowed_next"] is True
    assert tuple(material["implemented_steps"]) == dmh.P7_R54_AHR_POST_PMN23_DMH_OP12_IMPLEMENTED_STEPS
    assert tuple(material["not_yet_implemented_steps"]) == dmh.P7_R54_AHR_POST_PMN23_DMH_OP12_NOT_YET_IMPLEMENTED_STEPS
    assert material["next_required_step"] == dmh.P7_R54_AHR_POST_PMN23_DMH_OP13_STEP_REF
    for row in material["question_need_observation_rows"]:
        assert set(row) == set(dmh.P7_R54_AHR_POST_PMN23_DMH_OP12_QUESTION_NEED_OBSERVATION_ROW_REQUIRED_FIELD_REFS)
        assert row["schema_version"] == dmh.P7_R54_AHR_POST_PMN23_DMH_OP12_QUESTION_NEED_OBSERVATION_ROW_SCHEMA_VERSION
        assert row["body_free"] is True
        assert row["question_text_materialized_here"] is False
        assert row["draft_question_text_materialized_here"] is False
        assert row["question_trigger_logic_materialized_here"] is False
        assert row["question_answer_storage_materialized_here"] is False
        assert row["p8_implementation_spec_finalized_here"] is False
        assert row["p8_start_allowed"] is False
    _assert_bodyfree_no_touch_no_promotion(material)


def test_dmh_op12_alias_builder_matches_direct_contract() -> None:
    material = dmh.build_p7_r54_ahr_post_pmn23_downstream_manual_decision_hold_question_need_observation_rows_normalization_bodyfree(
        rating_rows_normalization_threshold_summary=_ready_op11(),
        sanitized_review_result_rows_intake=_ready_op10(),
    )

    assert material["dmh_op12_ready"] is True
    assert dmh.assert_p7_r54_ahr_post_pmn23_downstream_manual_decision_hold_question_need_observation_rows_normalization_bodyfree_contract(material) is True


def test_dmh_op12_keeps_p8_candidate_material_candidate_only_without_p8_start() -> None:
    op10, op11 = _op10_op11_with_mutated_source_row(
        lambda row: (
            row.__setitem__("question_need_primary_class_ref", "plus_single_question_candidate_later"),
            row.__setitem__("one_question_fit_ref", "fits_one_question"),
            row["plan_candidate_flags"].__setitem__("plus_single_question_candidate_later", True),
        )
    )
    material = dmh.build_p7_r54_ahr_post_pmn23_dmh_op12_question_need_observation_rows_normalization(
        rating_rows_normalization_threshold_summary=op11,
        sanitized_review_result_rows_intake=op10,
    )

    assert material["dmh_op12_ready"] is True
    assert material["p8_material_candidate_case_refs_bodyfree_only"] == ["cral_case_ref_001"]
    assert material["plus_single_question_candidate_case_refs_bodyfree_only"] == ["cral_case_ref_001"]
    assert material["p8_start_allowed"] is False
    assert material["question_text_materialized_here"] is False
    assert material["question_need_observation_rows"][0]["p8_material_candidate_only"] is True
    assert material["question_need_observation_rows"][0]["plus_single_question_candidate_later"] is True
    assert dmh.assert_p7_r54_ahr_post_pmn23_dmh_op12_question_need_observation_rows_normalization_contract(material) is True


def test_dmh_op12_blocks_without_op11_and_keeps_op13_closed() -> None:
    material = dmh.build_p7_r54_ahr_post_pmn23_dmh_op12_question_need_observation_rows_normalization(
        sanitized_review_result_rows_intake=_ready_op10(),
    )

    assert material["dmh_op12_ready"] is False
    assert material["dmh_op12_status_ref"] == dmh.P7_R54_AHR_POST_PMN23_DMH_OP12_BLOCKED_STATUS_REF
    assert "dmh_op12_rating_rows_normalization_missing" in material["dmh_op12_blocker_refs"]
    assert material["question_need_observation_rows"] == []
    assert material["rating_question_consistency_blocker_separation_allowed_next"] is False
    assert material["next_required_step"] == dmh.P7_R54_AHR_POST_PMN23_DMH_OP12_BLOCKED_NEXT_REQUIRED_STEP_REF
    assert dmh.assert_p7_r54_ahr_post_pmn23_dmh_op12_question_need_observation_rows_normalization_contract(material) is True
    _assert_bodyfree_no_touch_no_promotion(material)


def test_dmh_op12_blocks_without_op10_and_keeps_question_rows_closed() -> None:
    material = dmh.build_p7_r54_ahr_post_pmn23_dmh_op12_question_need_observation_rows_normalization(
        rating_rows_normalization_threshold_summary=_ready_op11(),
    )

    assert material["dmh_op12_ready"] is False
    assert "dmh_op12_sanitized_review_result_rows_intake_missing" in material["dmh_op12_blocker_refs"]
    assert material["question_need_observation_rows"] == []
    assert material["actual_question_need_observation_rows_materialized_from_actual_rows"] is False
    assert dmh.assert_p7_r54_ahr_post_pmn23_dmh_op12_question_need_observation_rows_normalization_contract(material) is True
    _assert_bodyfree_no_touch_no_promotion(material)


def test_dmh_op12_blocks_if_op11_question_next_permission_is_removed() -> None:
    op11 = _ready_op11()
    op11["question_need_observation_row_normalization_allowed_next"] = False
    material = dmh.build_p7_r54_ahr_post_pmn23_dmh_op12_question_need_observation_rows_normalization(
        rating_rows_normalization_threshold_summary=op11,
        sanitized_review_result_rows_intake=_ready_op10(),
    )

    assert material["dmh_op12_ready"] is False
    assert "dmh_op12_op11_rating_rows_normalization_invalid" in material["dmh_op12_blocker_refs"]
    assert material["next_required_step"] == dmh.P7_R54_AHR_POST_PMN23_DMH_OP12_BLOCKED_NEXT_REQUIRED_STEP_REF
    assert dmh.assert_p7_r54_ahr_post_pmn23_dmh_op12_question_need_observation_rows_normalization_contract(material) is True


@pytest.mark.parametrize(
    ("field", "bad_value"),
    [
        ("dmh_op12_ready", False),
        ("dmh_op12_status_ref", dmh.P7_R54_AHR_POST_PMN23_DMH_OP12_BLOCKED_STATUS_REF),
        ("question_need_observation_row_count", 23),
        ("question_need_observation_row_count_is_24", False),
        ("question_text_materialized_here", True),
        ("draft_question_text_materialized_here", True),
        ("question_trigger_logic_materialized_here", True),
        ("question_answer_storage_materialized_here", True),
        ("p8_implementation_spec_finalized_here", True),
        ("p8_start_allowed", True),
        ("actual_question_need_observation_rows_materialized_here", True),
        ("rating_question_consistency_blocker_separation_allowed_next", False),
        ("next_required_step", dmh.P7_R54_AHR_POST_PMN23_DMH_OP12_BLOCKED_NEXT_REQUIRED_STEP_REF),
    ],
)
def test_dmh_op12_contract_rejects_ready_material_mutations(field: str, bad_value: object) -> None:
    material = _ready_op12()
    material[field] = bad_value

    with pytest.raises(ValueError):
        dmh.assert_p7_r54_ahr_post_pmn23_dmh_op12_question_need_observation_rows_normalization_contract(material)


def test_dmh_op12_contract_rejects_question_row_body_or_question_mutation() -> None:
    material = _ready_op12()
    material["question_need_observation_rows"][0]["question_text_materialized_here"] = True

    with pytest.raises(ValueError):
        dmh.assert_p7_r54_ahr_post_pmn23_dmh_op12_question_need_observation_rows_normalization_contract(material)

    material = _ready_op12()
    material["question_need_observation_rows"][0]["raw_input"] = "must never be accepted"
    with pytest.raises(ValueError):
        dmh.assert_p7_r54_ahr_post_pmn23_dmh_op12_question_need_observation_rows_normalization_contract(material)


def test_dmh_op13_default_passes_without_blocker_rows_and_allows_disposal_next_only() -> None:
    material = _ready_op13()

    assert set(material) == set(dmh.P7_R54_AHR_POST_PMN23_DMH_OP13_REQUIRED_FIELD_REFS)
    assert material["schema_version"] == dmh.P7_R54_AHR_POST_PMN23_DMH_OP13_RATING_QUESTION_CONSISTENCY_BLOCKER_SEPARATION_SCHEMA_VERSION
    assert material["operation_step_ref"] == dmh.P7_R54_AHR_POST_PMN23_DMH_OP13_STEP_REF
    assert material["dmh_op13_status_ref"] == dmh.P7_R54_AHR_POST_PMN23_DMH_OP13_READY_STATUS_REF
    assert material["dmh_op13_ready"] is True
    assert material["rating_question_consistency_guard_passed"] is True
    assert material["dmh_op13_blocker_refs"] == []
    assert tuple(material["dmh_op13_reason_refs"]) == dmh.P7_R54_AHR_POST_PMN23_DMH_OP13_READY_REASON_REFS
    assert material["op12_dmh_ready"] is True
    assert material["op12_next_required_step"] == dmh.P7_R54_AHR_POST_PMN23_DMH_OP13_STEP_REF
    assert material["op12_p8_start_allowed"] is False
    assert material["op11_dmh_ready"] is True
    assert material["consistency_blocker_row_count"] == 0
    assert material["p8_material_candidate_case_count_bodyfree_only"] == 0
    assert material["p8_material_candidate_blocked_by_blocker_case_count"] == 0
    assert material["p8_material_candidate_allowed_after_blocker_separation_case_count"] == 0
    assert material["no_blocker_case_count"] == 24
    assert material["p5_repair_required_case_count"] == 0
    assert material["operation_blocked_case_count"] == 0
    assert material["rating_question_consistency_checked_here"] is True
    assert material["rating_question_consistency_guard_blocks_p8_escape"] is True
    assert material["question_observation_guard_does_not_create_question_text"] is True
    assert material["question_observation_guard_does_not_start_p8"] is True
    assert material["consistency_guard_does_not_create_disposal_or_evidence_complete"] is True
    assert material["actual_review_evidence_complete_from_real_review_still_false"] is True
    assert material["disposal_purge_receipt_intake_allowed_next"] is True
    assert tuple(material["implemented_steps"]) == dmh.P7_R54_AHR_POST_PMN23_DMH_OP13_IMPLEMENTED_STEPS
    assert tuple(material["not_yet_implemented_steps"]) == dmh.P7_R54_AHR_POST_PMN23_DMH_OP13_NOT_YET_IMPLEMENTED_STEPS
    assert material["next_required_step"] == dmh.P7_R54_AHR_POST_PMN23_DMH_OP14_STEP_REF
    _assert_bodyfree_no_touch_no_promotion(material)


def test_dmh_op13_alias_builder_matches_direct_contract() -> None:
    material = dmh.build_p7_r54_ahr_post_pmn23_downstream_manual_decision_hold_rating_question_consistency_blocker_separation_bodyfree(
        question_need_observation_rows_normalization=_ready_op12(),
        rating_rows_normalization_threshold_summary=_ready_op11(),
    )

    assert material["dmh_op13_ready"] is True
    assert dmh.assert_p7_r54_ahr_post_pmn23_downstream_manual_decision_hold_rating_question_consistency_blocker_separation_bodyfree_contract(material) is True


def test_dmh_op13_separates_below_target_p8_candidate_to_p5_repair_without_starting_p8() -> None:
    op10, op11 = _op10_op11_with_low_score_and_p8_candidate()
    op12, material = _op12_op13_from(op10, op11)

    assert op12["p8_material_candidate_case_refs_bodyfree_only"] == ["cral_case_ref_001"]
    assert material["dmh_op13_ready"] is True
    assert material["consistency_blocker_row_count"] == 1
    assert material["p8_material_candidate_case_refs_bodyfree_only"] == ["cral_case_ref_001"]
    assert material["p8_material_candidate_blocked_by_blocker_case_refs"] == ["cral_case_ref_001"]
    assert material["p8_material_candidate_allowed_after_blocker_separation_case_refs"] == []
    assert material["below_target_axis_p8_escape_blocked_count"] == 1
    assert material["p5_repair_required_case_refs"] == ["cral_case_ref_001"]
    row = material["consistency_blocker_rows"][0]
    assert row["blocker_kind_ref"] == "below_target_axis"
    assert row["blocker_category_ref"] == "p5_history_connection_weak"
    assert row["routes_to_ref"] == dmh.P7_R54_AHR_POST_PMN23_DMH_OP13_READFEEL_ROUTE_REF
    assert row["p8_candidate_escape_detected"] is True
    assert row["p8_candidate_escape_blocked"] is True
    assert row["p8_start_allowed"] is False
    assert material["p8_start_allowed"] is False
    assert material["next_required_step"] == dmh.P7_R54_AHR_POST_PMN23_DMH_OP14_STEP_REF


@pytest.mark.parametrize(
    ("mutation_name", "mutator", "expected_kind", "expected_category", "expected_count_field"),
    [
        (
            "safe_display_risk",
            lambda row: (
                row.__setitem__("question_need_primary_class_ref", "plus_single_question_candidate_later"),
                row.__setitem__("one_question_fit_ref", "fits_one_question"),
                row["safe_display_check_refs"].__setitem__(0, "safe_display_risk_detected"),
            ),
            "safe_display_risk",
            "p5_safe_display_risk",
            "safe_display_question_escape_blocked_count",
        ),
        (
            "readfeel_blocker",
            lambda row: (
                row.__setitem__("question_need_primary_class_ref", "question_may_reduce_overread_risk"),
                row.__setitem__("one_question_fit_ref", "fits_one_question"),
                row["readfeel_blocker_ids"].append("history_connection_weak"),
            ),
            "readfeel_blocker",
            "p5_history_connection_weak",
            "readfeel_blocker_question_escape_blocked_count",
        ),
        (
            "execution_blocker",
            lambda row: (
                row.__setitem__("question_need_primary_class_ref", "question_may_reduce_overread_risk"),
                row.__setitem__("one_question_fit_ref", "fits_one_question"),
                row["execution_blocker_ids"].append("reviewer_selection_incomplete"),
            ),
            "execution_blocker",
            "operation_blocked_missing_receipt",
            "execution_blocker_question_escape_blocked_count",
        ),
        (
            "repair_required",
            lambda row: (
                row.__setitem__("question_need_primary_class_ref", "question_may_reduce_overread_risk"),
                row.__setitem__("one_question_fit_ref", "fits_one_question"),
                row["repair_required_refs"].append("p4_current_surface_repair_required"),
            ),
            "repair_required",
            "p4_current_only_surface_repair_required",
            "repair_required_question_escape_blocked_count",
        ),
    ],
)
def test_dmh_op13_separates_blocker_categories_without_question_or_p8_promotion(
    mutation_name: str,
    mutator,
    expected_kind: str,
    expected_category: str,
    expected_count_field: str,
) -> None:
    op10, op11 = _op10_op11_with_mutated_source_row(mutator)
    _, material = _op12_op13_from(op10, op11)

    assert material["dmh_op13_ready"] is True, mutation_name
    assert material["consistency_blocker_row_count"] >= 1
    assert material["p8_material_candidate_blocked_by_blocker_case_refs"] == ["cral_case_ref_001"]
    assert material[expected_count_field] >= 1
    assert material["p8_start_allowed"] is False
    row = material["consistency_blocker_rows"][0]
    assert row["blocker_kind_ref"] == expected_kind
    assert row["blocker_category_ref"] == expected_category
    assert row["question_text_materialized_here"] is False
    assert row["p8_start_allowed"] is False
    assert dmh.assert_p7_r54_ahr_post_pmn23_dmh_op13_rating_question_consistency_blocker_separation_contract(material) is True


def test_dmh_op13_blocks_without_op12_and_keeps_disposal_closed() -> None:
    material = dmh.build_p7_r54_ahr_post_pmn23_dmh_op13_rating_question_consistency_blocker_separation(
        rating_rows_normalization_threshold_summary=_ready_op11(),
    )

    assert material["dmh_op13_ready"] is False
    assert material["dmh_op13_status_ref"] == dmh.P7_R54_AHR_POST_PMN23_DMH_OP13_BLOCKED_STATUS_REF
    assert "dmh_op13_question_need_observation_rows_normalization_missing" in material["dmh_op13_blocker_refs"]
    assert material["rating_question_consistency_guard_passed"] is False
    assert material["disposal_purge_receipt_intake_allowed_next"] is False
    assert material["consistency_blocker_rows"] == []
    assert material["next_required_step"] == dmh.P7_R54_AHR_POST_PMN23_DMH_OP13_BLOCKED_NEXT_REQUIRED_STEP_REF
    assert dmh.assert_p7_r54_ahr_post_pmn23_dmh_op13_rating_question_consistency_blocker_separation_contract(material) is True
    _assert_bodyfree_no_touch_no_promotion(material)


def test_dmh_op13_blocks_if_op12_material_was_mutated_after_normalization() -> None:
    op12 = _ready_op12()
    op12["question_need_observation_rows"][0]["raw_input"] = "must not pass into consistency guard"
    material = dmh.build_p7_r54_ahr_post_pmn23_dmh_op13_rating_question_consistency_blocker_separation(
        question_need_observation_rows_normalization=op12,
        rating_rows_normalization_threshold_summary=_ready_op11(),
    )

    assert material["dmh_op13_ready"] is False
    assert "dmh_op13_op12_question_need_observation_rows_normalization_invalid" in material["dmh_op13_blocker_refs"]
    assert material["disposal_purge_receipt_intake_allowed_next"] is False
    assert dmh.assert_p7_r54_ahr_post_pmn23_dmh_op13_rating_question_consistency_blocker_separation_contract(material) is True


@pytest.mark.parametrize(
    ("field", "bad_value"),
    [
        ("dmh_op13_ready", False),
        ("dmh_op13_status_ref", dmh.P7_R54_AHR_POST_PMN23_DMH_OP13_BLOCKED_STATUS_REF),
        ("rating_question_consistency_guard_passed", False),
        ("rating_question_consistency_checked_here", False),
        ("rating_question_consistency_guard_blocks_p8_escape", False),
        ("p5_repair_required_cases_routed_to_p5_repair", False),
        ("p4_repair_required_cases_routed_to_p4_repair", False),
        ("safe_display_risk_cases_not_routed_to_p8", False),
        ("operation_blocker_cases_not_routed_to_p8", False),
        ("question_observation_guard_does_not_create_question_text", False),
        ("question_observation_guard_does_not_start_p8", False),
        ("disposal_purge_receipt_intake_allowed_next", False),
        ("p8_start_allowed", True),
        ("release_allowed", True),
        ("next_required_step", dmh.P7_R54_AHR_POST_PMN23_DMH_OP13_BLOCKED_NEXT_REQUIRED_STEP_REF),
    ],
)
def test_dmh_op13_contract_rejects_ready_material_mutations(field: str, bad_value: object) -> None:
    material = _ready_op13()
    material[field] = bad_value

    with pytest.raises(ValueError):
        dmh.assert_p7_r54_ahr_post_pmn23_dmh_op13_rating_question_consistency_blocker_separation_contract(material)


def test_dmh_op13_contract_rejects_consistency_blocker_row_mutations() -> None:
    op10, op11 = _op10_op11_with_low_score_and_p8_candidate()
    _, material = _op12_op13_from(op10, op11)
    material["consistency_blocker_rows"][0]["question_text_materialized_here"] = True

    with pytest.raises(ValueError):
        dmh.assert_p7_r54_ahr_post_pmn23_dmh_op13_rating_question_consistency_blocker_separation_contract(material)

    _, material = _op12_op13_from(op10, op11)
    material["consistency_blocker_rows"][0]["packet_content"] = "must never be accepted"
    with pytest.raises(ValueError):
        dmh.assert_p7_r54_ahr_post_pmn23_dmh_op13_rating_question_consistency_blocker_separation_contract(material)
