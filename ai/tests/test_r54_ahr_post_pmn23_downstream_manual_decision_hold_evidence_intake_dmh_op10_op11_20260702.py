# -*- coding: utf-8 -*-
"""R54-AHR Post-PMN23 downstream manual decision hold DMH-OP10/OP11 tests."""

from __future__ import annotations

from copy import deepcopy
from pathlib import Path
import sys

import pytest

TEST_DIR = Path(__file__).resolve().parent
if str(TEST_DIR) not in sys.path:
    sys.path.insert(0, str(TEST_DIR))

import emlis_ai_p7_r54_ahr_post_pmn23_downstream_manual_decision_hold_evidence_intake_20260701 as dmh
import test_r54_ahr_post_pmn23_downstream_manual_decision_hold_evidence_intake_dmh_op08_op09_20260702 as dmh_op08_op09_prev

_READY_OP09_CACHE: dict[str, object] | None = None
_READY_ROWS_CACHE: list[dict[str, object]] | None = None
_READY_OP10_CACHE: dict[str, object] | None = None
_READY_OP11_CACHE: dict[str, object] | None = None


def _ready_op09() -> dict[str, object]:
    global _READY_OP09_CACHE
    if _READY_OP09_CACHE is None:
        material = dmh_op08_op09_prev._ready_op09()
        assert dmh.assert_p7_r54_ahr_post_pmn23_dmh_op09_actual_operation_receipt_intake_contract(material) is True
        _READY_OP09_CACHE = material
    return deepcopy(_READY_OP09_CACHE)


def _ready_rows() -> list[dict[str, object]]:
    global _READY_ROWS_CACHE
    if _READY_ROWS_CACHE is None:
        op09 = _ready_op09()
        rows = dmh.build_p7_r54_ahr_post_pmn23_dmh_op10_sanitized_review_result_rows_bodyfree(
            review_session_id=op09["review_session_id"],
            operation_receipt_ref=op09["operation_receipt_ref"],
            reviewer_person_ref=op09["reviewer_person_ref"],
        )
        _READY_ROWS_CACHE = rows
    return deepcopy(_READY_ROWS_CACHE)


def _ready_op10() -> dict[str, object]:
    global _READY_OP10_CACHE
    if _READY_OP10_CACHE is None:
        material = dmh.build_p7_r54_ahr_post_pmn23_dmh_op10_sanitized_review_result_rows_intake_provenance_guard(
            actual_operation_receipt_intake=_ready_op09(),
            sanitized_review_result_rows_bodyfree=_ready_rows(),
        )
        assert dmh.assert_p7_r54_ahr_post_pmn23_dmh_op10_sanitized_review_result_rows_intake_provenance_guard_contract(material) is True
        _READY_OP10_CACHE = material
    return deepcopy(_READY_OP10_CACHE)


def _ready_op11() -> dict[str, object]:
    global _READY_OP11_CACHE
    if _READY_OP11_CACHE is None:
        material = dmh.build_p7_r54_ahr_post_pmn23_dmh_op11_rating_rows_normalization_threshold_summary(
            sanitized_review_result_rows_intake=_ready_op10(),
        )
        assert dmh.assert_p7_r54_ahr_post_pmn23_dmh_op11_rating_rows_normalization_threshold_summary_contract(material) is True
        _READY_OP11_CACHE = material
    return deepcopy(_READY_OP11_CACHE)


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


def test_dmh_op10_sanitized_review_result_rows_fixture_shape_is_bodyfree_actual_person_source() -> None:
    rows = _ready_rows()

    assert len(rows) == 24
    assert {row["case_ref_id"] for row in rows} == {f"cral_case_ref_{index:03d}" for index in range(1, 25)}
    assert {row["blind_case_id"] for row in rows} == {f"cral_blind_case_{index:03d}" for index in range(1, 25)}
    assert {row["packet_ref_id"] for row in rows} == {f"cral_packet_ref_{index:03d}" for index in range(1, 25)}
    for row in rows:
        assert set(row) == set(dmh.P7_R54_AHR_POST_PMN23_DMH_OP10_REQUIRED_SANITIZED_ROW_FIELD_REFS)
        assert row["schema_version"] == dmh.P7_R54_AHR_POST_PMN23_DMH_OP10_SANITIZED_REVIEW_RESULT_ROW_SCHEMA_VERSION
        assert row["row_source_ref"] == dmh.P7_R54_AHR_POST_PMN23_DMH_OP10_ALLOWED_ROW_SOURCE_REF
        assert row["row_created_by_helper"] is False
        assert row["row_created_for_unit_test"] is False
        assert row["row_is_synthetic_contract_fixture"] is False
        assert row["historical_row_reused"] is False
        assert row["selection_only"] is True
        assert row["selection_only_row"] is True
        assert row["body_free"] is True
        assert row["axis_score_count"] == 6
        assert set(row["axis_scores"]) == set(dmh.P7_R54_AHR_POST_PMN23_DMH_OP07_RATING_AXIS_REFS)
        assert all(value is False for key, value in row.items() if key.endswith("_included") or key.endswith("_materialized_here") or key == "p8_implementation_spec_finalized_here")


def test_dmh_op10_accepts_24_actual_person_selection_only_rows_and_allows_rating_next() -> None:
    material = _ready_op10()

    assert set(material) == set(dmh.P7_R54_AHR_POST_PMN23_DMH_OP10_REQUIRED_FIELD_REFS)
    assert material["schema_version"] == dmh.P7_R54_AHR_POST_PMN23_DMH_OP10_SANITIZED_REVIEW_RESULT_ROWS_INTAKE_PROVENANCE_GUARD_SCHEMA_VERSION
    assert material["operation_step_ref"] == dmh.P7_R54_AHR_POST_PMN23_DMH_OP10_STEP_REF
    assert material["dmh_op10_status_ref"] == dmh.P7_R54_AHR_POST_PMN23_DMH_OP10_READY_STATUS_REF
    assert material["dmh_op10_ready"] is True
    assert material["dmh_op10_blocker_refs"] == []
    assert tuple(material["dmh_op10_reason_refs"]) == dmh.P7_R54_AHR_POST_PMN23_DMH_OP10_READY_REASON_REFS
    assert material["op09_dmh_ready"] is True
    assert material["op09_next_required_step"] == dmh.P7_R54_AHR_POST_PMN23_DMH_OP10_STEP_REF
    assert material["op09_actual_human_review_executed_by_person"] is True
    assert material["sanitized_review_result_rows_input_present"] is True
    assert material["received_sanitized_review_result_row_count"] == 24
    assert material["sanitized_review_result_row_count"] == 24
    assert material["sanitized_review_result_row_count_is_24"] is True
    assert material["review_result_row_ref_count"] == 24
    assert material["case_ref_id_count"] == 24
    assert material["case_ref_ids_unique"] is True
    assert material["blind_case_id_count"] == 24
    assert material["blind_case_ids_unique"] is True
    assert material["packet_ref_id_count"] == 24
    assert material["packet_ref_ids_unique"] is True
    assert material["rows_match_24_case_manifest"] is True
    assert material["rows_bodyfree_only"] is True
    assert material["rows_selection_only"] is True
    assert material["rows_have_actual_person_selection_only_provenance"] is True
    assert material["rows_have_required_axis_scores"] is True
    assert material["rows_have_allowed_verdict_refs"] is True
    assert material["rows_have_allowed_label_connection_refs"] is True
    assert material["rows_have_allowed_safe_display_refs"] is True
    assert material["rows_have_allowed_question_observation_refs"] is True
    assert material["rows_have_no_body_or_question_or_path_or_hash"] is True
    assert material["row_provenance_guard_passed"] is True
    assert material["sanitized_selection_only_result_rows_intaken_here"] is True
    assert material["actual_sanitized_review_result_rows_intaken_here"] is True
    assert material["actual_selection_rows_created_here"] is False
    assert material["actual_sanitized_review_result_rows_created_here"] is False
    assert material["rating_row_normalization_allowed_next"] is True
    assert material["actual_review_evidence_complete_from_real_review_still_false"] is True
    assert tuple(material["implemented_steps"]) == dmh.P7_R54_AHR_POST_PMN23_DMH_OP10_IMPLEMENTED_STEPS
    assert tuple(material["not_yet_implemented_steps"]) == dmh.P7_R54_AHR_POST_PMN23_DMH_OP10_NOT_YET_IMPLEMENTED_STEPS
    assert material["next_required_step"] == dmh.P7_R54_AHR_POST_PMN23_DMH_OP11_STEP_REF
    for row in material["review_result_rows"]:
        assert set(row) == set(dmh.P7_R54_AHR_POST_PMN23_DMH_OP10_REQUIRED_SANITIZED_ROW_FIELD_REFS)
        assert row["row_source_ref"] == dmh.P7_R54_AHR_POST_PMN23_DMH_OP10_ALLOWED_ROW_SOURCE_REF
        assert row["body_free"] is True
    _assert_bodyfree_no_touch_no_promotion(material)


def test_dmh_op10_alias_builders_match_direct_contract() -> None:
    material = dmh.build_p7_r54_ahr_post_pmn23_downstream_manual_decision_hold_sanitized_review_result_rows_intake_provenance_guard_bodyfree(
        actual_operation_receipt_intake=_ready_op09(),
        sanitized_review_result_rows_bodyfree=_ready_rows(),
    )

    assert material["dmh_op10_ready"] is True
    assert dmh.assert_p7_r54_ahr_post_pmn23_downstream_manual_decision_hold_sanitized_review_result_rows_intake_provenance_guard_bodyfree_contract(material) is True


def test_dmh_op10_blocks_without_operation_receipt_intake() -> None:
    material = dmh.build_p7_r54_ahr_post_pmn23_dmh_op10_sanitized_review_result_rows_intake_provenance_guard(
        sanitized_review_result_rows_bodyfree=_ready_rows(),
    )

    assert material["dmh_op10_ready"] is False
    assert material["dmh_op10_status_ref"] == dmh.P7_R54_AHR_POST_PMN23_DMH_OP10_BLOCKED_STATUS_REF
    assert "dmh_op10_actual_operation_receipt_intake_missing" in material["dmh_op10_blocker_refs"]
    assert material["sanitized_selection_only_result_rows_intaken_here"] is False
    assert material["rating_row_normalization_allowed_next"] is False
    assert material["next_required_step"] == dmh.P7_R54_AHR_POST_PMN23_DMH_OP10_BLOCKED_NEXT_REQUIRED_STEP_REF
    assert dmh.assert_p7_r54_ahr_post_pmn23_dmh_op10_sanitized_review_result_rows_intake_provenance_guard_contract(material) is True
    _assert_bodyfree_no_touch_no_promotion(material)


def test_dmh_op10_blocks_without_sanitized_rows_and_keeps_rating_closed() -> None:
    material = dmh.build_p7_r54_ahr_post_pmn23_dmh_op10_sanitized_review_result_rows_intake_provenance_guard(
        actual_operation_receipt_intake=_ready_op09(),
    )

    assert material["dmh_op10_ready"] is False
    assert "dmh_op10_sanitized_review_result_rows_not_received" in material["dmh_op10_blocker_refs"]
    assert material["sanitized_review_result_rows_input_present"] is False
    assert material["rating_row_normalization_allowed_next"] is False
    assert dmh.assert_p7_r54_ahr_post_pmn23_dmh_op10_sanitized_review_result_rows_intake_provenance_guard_contract(material) is True
    _assert_bodyfree_no_touch_no_promotion(material)


@pytest.mark.parametrize(
    ("mutation_name", "mutate_rows", "expected_blocker", "expected_status"),
    [
        ("row_count", lambda rows: rows.pop(), "dmh_op10_sanitized_review_result_row_count_not_24", dmh.P7_R54_AHR_POST_PMN23_DMH_OP10_BLOCKED_STATUS_REF),
        ("wrong_source", lambda rows: rows[0].__setitem__("row_source_ref", "helper_default_fixture_rows"), "dmh_op10_sanitized_row_source_ref_not_actual_person_selection_only_rows_local_review", dmh.P7_R54_AHR_POST_PMN23_DMH_OP10_BLOCKED_STATUS_REF),
        ("helper_row", lambda rows: rows[0].__setitem__("row_created_by_helper", True), "dmh_op10_sanitized_row_created_by_helper_cannot_be_actual", dmh.P7_R54_AHR_POST_PMN23_DMH_OP10_BLOCKED_STATUS_REF),
        ("unit_test_row", lambda rows: rows[0].__setitem__("row_created_for_unit_test", True), "dmh_op10_sanitized_row_created_for_unit_test_cannot_be_actual", dmh.P7_R54_AHR_POST_PMN23_DMH_OP10_BLOCKED_STATUS_REF),
        ("synthetic_row", lambda rows: rows[0].__setitem__("row_is_synthetic_contract_fixture", True), "dmh_op10_sanitized_row_is_synthetic_contract_fixture_cannot_be_actual", dmh.P7_R54_AHR_POST_PMN23_DMH_OP10_BLOCKED_STATUS_REF),
        ("historical_row", lambda rows: rows[0].__setitem__("historical_row_reused", True), "dmh_op10_sanitized_row_historical_row_reused_cannot_be_actual", dmh.P7_R54_AHR_POST_PMN23_DMH_OP10_BLOCKED_STATUS_REF),
        ("session_mismatch", lambda rows: rows[0].__setitem__("review_session_id", "different_session_bodyfree"), "dmh_op10_sanitized_row_review_session_id_mismatch", dmh.P7_R54_AHR_POST_PMN23_DMH_OP10_BLOCKED_STATUS_REF),
        ("operation_receipt_mismatch", lambda rows: rows[0].__setitem__("operation_receipt_ref", "different_receipt_bodyfree"), "dmh_op10_sanitized_row_operation_receipt_ref_mismatch", dmh.P7_R54_AHR_POST_PMN23_DMH_OP10_BLOCKED_STATUS_REF),
        ("reviewer_mismatch", lambda rows: rows[0].__setitem__("reviewer_person_ref", "different_reviewer_bodyfree"), "dmh_op10_sanitized_row_reviewer_person_ref_mismatch", dmh.P7_R54_AHR_POST_PMN23_DMH_OP10_BLOCKED_STATUS_REF),
        ("manifest_mismatch", lambda rows: rows[0].__setitem__("case_ref_id", "cral_case_ref_999"), "dmh_op10_sanitized_row_manifest_id_mismatch", dmh.P7_R54_AHR_POST_PMN23_DMH_OP10_BLOCKED_STATUS_REF),
        ("axis_out_of_range", lambda rows: rows[0]["axis_scores"].__setitem__(dmh.P7_R54_AHR_POST_PMN23_DMH_OP07_RATING_AXIS_REFS[0], 2.0), "dmh_op10_sanitized_row_axis_scores_missing_or_out_of_range", dmh.P7_R54_AHR_POST_PMN23_DMH_OP10_BLOCKED_STATUS_REF),
        ("axis_count_wrong", lambda rows: rows[0].__setitem__("axis_score_count", 5), "dmh_op10_sanitized_row_axis_scores_missing_or_out_of_range", dmh.P7_R54_AHR_POST_PMN23_DMH_OP10_BLOCKED_STATUS_REF),
        ("verdict_bad", lambda rows: rows[0].__setitem__("verdict_ref", "BAD"), "dmh_op10_sanitized_row_verdict_ref_not_allowed", dmh.P7_R54_AHR_POST_PMN23_DMH_OP10_BLOCKED_STATUS_REF),
        ("question_class_bad", lambda rows: rows[0].__setitem__("question_need_primary_class_ref", "bad_question_class"), "dmh_op10_sanitized_row_question_need_primary_class_ref_not_allowed", dmh.P7_R54_AHR_POST_PMN23_DMH_OP10_BLOCKED_STATUS_REF),
        ("raw_body_key", lambda rows: rows[0].__setitem__("raw_input", "must never be accepted"), "dmh_op10_sanitized_rows_forbidden_body_question_path_hash_key_detected", dmh.P7_R54_AHR_POST_PMN23_DMH_OP10_BLOCKED_BY_LEAK_STATUS_REF),
        ("question_flag", lambda rows: rows[0].__setitem__("question_text_included", True), "dmh_op10_sanitized_row_required_fields_mismatch", dmh.P7_R54_AHR_POST_PMN23_DMH_OP10_BLOCKED_STATUS_REF),
        ("selection_only_false", lambda rows: rows[0].__setitem__("selection_only", False), "dmh_op10_sanitized_row_selection_only_not_true", dmh.P7_R54_AHR_POST_PMN23_DMH_OP10_BLOCKED_STATUS_REF),
        ("body_free_false", lambda rows: rows[0].__setitem__("body_free", False), "dmh_op10_sanitized_row_body_free_not_true", dmh.P7_R54_AHR_POST_PMN23_DMH_OP10_BLOCKED_STATUS_REF),
    ],
)
def test_dmh_op10_blocks_invalid_sanitized_rows_without_rating_promotion(
    mutation_name: str,
    mutate_rows,
    expected_blocker: str,
    expected_status: str,
) -> None:
    rows = _ready_rows()
    mutate_rows(rows)
    material = dmh.build_p7_r54_ahr_post_pmn23_dmh_op10_sanitized_review_result_rows_intake_provenance_guard(
        actual_operation_receipt_intake=_ready_op09(),
        sanitized_review_result_rows_bodyfree=rows,
    )

    assert material["dmh_op10_ready"] is False, mutation_name
    assert material["dmh_op10_status_ref"] == expected_status
    assert expected_blocker in material["dmh_op10_blocker_refs"]
    assert material["sanitized_selection_only_result_rows_intaken_here"] is False
    assert material["actual_sanitized_review_result_rows_intaken_here"] is False
    assert material["rating_row_normalization_allowed_next"] is False
    assert material["next_required_step"] == dmh.P7_R54_AHR_POST_PMN23_DMH_OP10_BLOCKED_NEXT_REQUIRED_STEP_REF
    assert dmh.assert_p7_r54_ahr_post_pmn23_dmh_op10_sanitized_review_result_rows_intake_provenance_guard_contract(material) is True


@pytest.mark.parametrize(
    ("field", "bad_value"),
    [
        ("dmh_op10_ready", False),
        ("dmh_op10_status_ref", dmh.P7_R54_AHR_POST_PMN23_DMH_OP10_BLOCKED_STATUS_REF),
        ("sanitized_review_result_row_count", 23),
        ("sanitized_review_result_row_count_is_24", False),
        ("rows_have_actual_person_selection_only_provenance", False),
        ("rows_have_no_body_or_question_or_path_or_hash", False),
        ("row_provenance_guard_passed", False),
        ("sanitized_selection_only_result_rows_intaken_here", False),
        ("actual_sanitized_review_result_rows_intaken_here", False),
        ("actual_sanitized_review_result_rows_created_here", True),
        ("rating_row_normalization_allowed_next", False),
        ("p8_start_allowed", True),
        ("release_allowed", True),
        ("next_required_step", dmh.P7_R54_AHR_POST_PMN23_DMH_OP10_BLOCKED_NEXT_REQUIRED_STEP_REF),
    ],
)
def test_dmh_op10_contract_rejects_ready_material_mutations(field: str, bad_value: object) -> None:
    material = _ready_op10()
    material[field] = bad_value

    with pytest.raises(ValueError):
        dmh.assert_p7_r54_ahr_post_pmn23_dmh_op10_sanitized_review_result_rows_intake_provenance_guard_contract(material)


def test_dmh_op10_contract_rejects_row_shape_mutation_after_intake() -> None:
    material = _ready_op10()
    material["review_result_rows"][0]["raw_input"] = "must not be normalized later"

    with pytest.raises(ValueError):
        dmh.assert_p7_r54_ahr_post_pmn23_dmh_op10_sanitized_review_result_rows_intake_provenance_guard_contract(material)


def test_dmh_op11_normalizes_rating_rows_and_keeps_rating_as_decision_material_only() -> None:
    material = _ready_op11()

    assert set(material) == set(dmh.P7_R54_AHR_POST_PMN23_DMH_OP11_REQUIRED_FIELD_REFS)
    assert material["schema_version"] == dmh.P7_R54_AHR_POST_PMN23_DMH_OP11_RATING_ROWS_NORMALIZATION_THRESHOLD_SUMMARY_SCHEMA_VERSION
    assert material["operation_step_ref"] == dmh.P7_R54_AHR_POST_PMN23_DMH_OP11_STEP_REF
    assert material["dmh_op11_status_ref"] == dmh.P7_R54_AHR_POST_PMN23_DMH_OP11_READY_STATUS_REF
    assert material["dmh_op11_ready"] is True
    assert material["dmh_op11_blocker_refs"] == []
    assert tuple(material["dmh_op11_reason_refs"]) == dmh.P7_R54_AHR_POST_PMN23_DMH_OP11_READY_REASON_REFS
    assert material["op10_dmh_ready"] is True
    assert material["op10_next_required_step"] == dmh.P7_R54_AHR_POST_PMN23_DMH_OP11_STEP_REF
    assert material["op10_sanitized_review_result_row_count"] == 24
    assert material["rating_row_count"] == 24
    assert material["required_rating_row_count"] == 24
    assert material["rating_row_count_is_24"] is True
    assert material["rating_row_ref_count"] == 24
    assert material["axis_ref_count"] == 6
    assert material["axis_score_count_per_row"] == 6
    assert material["axis_target_thresholds_present"] is True
    assert material["all_axis_target_passed"] is True
    assert material["below_target_axis_refs"] == []
    assert material["actual_rating_rows_materialized_from_actual_rows"] is True
    assert material["rating_rows_normalized_here"] is True
    assert material["rating_decision_material_only"] is True
    assert material["p5_final_allowed"] is False
    assert material["p5_finalization_still_manual_decision_required"] is True
    assert material["question_need_observation_row_normalization_allowed_next"] is True
    assert material["actual_review_evidence_complete_from_real_review_still_false"] is True
    assert tuple(material["implemented_steps"]) == dmh.P7_R54_AHR_POST_PMN23_DMH_OP11_IMPLEMENTED_STEPS
    assert tuple(material["not_yet_implemented_steps"]) == dmh.P7_R54_AHR_POST_PMN23_DMH_OP11_NOT_YET_IMPLEMENTED_STEPS
    assert material["next_required_step"] == dmh.P7_R54_AHR_POST_PMN23_DMH_OP12_STEP_REF
    assert material["label_connection_distribution_ref"]["label_connection_present_natural"] == 24
    assert material["verdict_distribution_ref"]["PASS"] == 24
    for row in material["rating_rows"]:
        assert set(row) == set(dmh.P7_R54_AHR_POST_PMN23_DMH_OP11_REQUIRED_RATING_ROW_FIELD_REFS)
        assert row["schema_version"] == dmh.P7_R54_AHR_POST_PMN23_DMH_OP11_RATING_ROW_SCHEMA_VERSION
        assert row["row_source_ref"] == dmh.P7_R54_AHR_POST_PMN23_DMH_OP10_ALLOWED_ROW_SOURCE_REF
        assert row["rating_decision_material_only"] is True
        assert row["body_free"] is True
    _assert_bodyfree_no_touch_no_promotion(material)


def test_dmh_op11_low_axis_score_keeps_ready_but_reports_threshold_summary() -> None:
    op09 = _ready_op09()
    target_axis = dmh.P7_R54_AHR_POST_PMN23_DMH_OP07_RATING_AXIS_REFS[0]
    rows = dmh.build_p7_r54_ahr_post_pmn23_dmh_op10_sanitized_review_result_rows_bodyfree(
        review_session_id=op09["review_session_id"],
        operation_receipt_ref=op09["operation_receipt_ref"],
        reviewer_person_ref=op09["reviewer_person_ref"],
        score_overrides_by_index={1: {target_axis: 0.5}},
    )
    op10 = dmh.build_p7_r54_ahr_post_pmn23_dmh_op10_sanitized_review_result_rows_intake_provenance_guard(
        actual_operation_receipt_intake=op09,
        sanitized_review_result_rows_bodyfree=rows,
    )
    material = dmh.build_p7_r54_ahr_post_pmn23_dmh_op11_rating_rows_normalization_threshold_summary(
        sanitized_review_result_rows_intake=op10,
    )

    assert op10["dmh_op10_ready"] is True
    assert material["dmh_op11_ready"] is True
    assert material["all_axis_target_passed"] is False
    assert material["below_target_axis_refs"] == [target_axis]
    assert material["axis_pass_summary"][target_axis]["below_target"] == 1
    assert material["axis_pass_summary"][target_axis]["passed"] == 23
    assert dmh.assert_p7_r54_ahr_post_pmn23_dmh_op11_rating_rows_normalization_threshold_summary_contract(material) is True


def test_dmh_op11_alias_builder_matches_direct_contract() -> None:
    material = dmh.build_p7_r54_ahr_post_pmn23_downstream_manual_decision_hold_rating_rows_normalization_threshold_summary_bodyfree(
        sanitized_review_result_rows_intake=_ready_op10(),
    )

    assert material["dmh_op11_ready"] is True
    assert dmh.assert_p7_r54_ahr_post_pmn23_downstream_manual_decision_hold_rating_rows_normalization_threshold_summary_bodyfree_contract(material) is True


def test_dmh_op11_blocks_without_op10_and_keeps_question_rows_closed() -> None:
    material = dmh.build_p7_r54_ahr_post_pmn23_dmh_op11_rating_rows_normalization_threshold_summary()

    assert material["dmh_op11_ready"] is False
    assert material["dmh_op11_status_ref"] == dmh.P7_R54_AHR_POST_PMN23_DMH_OP11_BLOCKED_STATUS_REF
    assert "dmh_op11_sanitized_review_result_rows_intake_missing" in material["dmh_op11_blocker_refs"]
    assert material["rating_rows"] == []
    assert material["rating_rows_normalized_here"] is False
    assert material["actual_rating_rows_materialized_from_actual_rows"] is False
    assert material["question_need_observation_row_normalization_allowed_next"] is False
    assert material["next_required_step"] == dmh.P7_R54_AHR_POST_PMN23_DMH_OP11_BLOCKED_NEXT_REQUIRED_STEP_REF
    assert dmh.assert_p7_r54_ahr_post_pmn23_dmh_op11_rating_rows_normalization_threshold_summary_contract(material) is True
    _assert_bodyfree_no_touch_no_promotion(material)


def test_dmh_op11_blocks_if_op10_material_was_mutated_after_provenance_guard() -> None:
    op10 = _ready_op10()
    op10["review_result_rows"][0]["raw_input"] = "must not be accepted downstream"
    material = dmh.build_p7_r54_ahr_post_pmn23_dmh_op11_rating_rows_normalization_threshold_summary(
        sanitized_review_result_rows_intake=op10,
    )

    assert material["dmh_op11_ready"] is False
    assert "dmh_op11_op10_sanitized_review_result_rows_contract_invalid" in material["dmh_op11_blocker_refs"]
    assert material["rating_rows"] == []
    assert material["rating_rows_normalized_here"] is False
    assert material["question_need_observation_row_normalization_allowed_next"] is False
    assert dmh.assert_p7_r54_ahr_post_pmn23_dmh_op11_rating_rows_normalization_threshold_summary_contract(material) is True


@pytest.mark.parametrize(
    ("field", "bad_value"),
    [
        ("dmh_op11_ready", False),
        ("dmh_op11_status_ref", dmh.P7_R54_AHR_POST_PMN23_DMH_OP11_BLOCKED_STATUS_REF),
        ("rating_row_count", 23),
        ("rating_row_count_is_24", False),
        ("axis_target_thresholds_present", False),
        ("actual_rating_rows_materialized_from_actual_rows", False),
        ("actual_rating_rows_materialized_here", True),
        ("rating_rows_normalized_here", False),
        ("rating_decision_material_only", False),
        ("p5_final_allowed", True),
        ("question_need_observation_row_normalization_allowed_next", False),
        ("p8_start_allowed", True),
        ("release_allowed", True),
        ("next_required_step", dmh.P7_R54_AHR_POST_PMN23_DMH_OP11_BLOCKED_NEXT_REQUIRED_STEP_REF),
    ],
)
def test_dmh_op11_contract_rejects_ready_material_mutations(field: str, bad_value: object) -> None:
    material = _ready_op11()
    material[field] = bad_value

    with pytest.raises(ValueError):
        dmh.assert_p7_r54_ahr_post_pmn23_dmh_op11_rating_rows_normalization_threshold_summary_contract(material)


def test_dmh_op11_contract_rejects_rating_row_shape_mutation() -> None:
    material = _ready_op11()
    material["rating_rows"][0]["packet_content"] = "must never be accepted"

    with pytest.raises(ValueError):
        dmh.assert_p7_r54_ahr_post_pmn23_dmh_op11_rating_rows_normalization_threshold_summary_contract(material)
