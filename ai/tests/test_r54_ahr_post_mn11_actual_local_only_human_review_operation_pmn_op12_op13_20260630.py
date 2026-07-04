# -*- coding: utf-8 -*-
"""R54-AHR Post-MN11 actual local-only human review operation PMN-OP12/OP13 tests."""

from __future__ import annotations

from copy import deepcopy
from pathlib import Path
import sys

import pytest

TEST_DIR = Path(__file__).resolve().parent
if str(TEST_DIR) not in sys.path:
    sys.path.insert(0, str(TEST_DIR))

import emlis_ai_p7_r54_ahr_post_mn11_actual_local_only_human_review_operation_20260630 as pmn
import test_r54_ahr_post_mn11_actual_local_only_human_review_operation_pmn_op10_op11_20260630 as prev


def _assert_bodyfree_no_touch_no_promotion(material: dict[str, object]) -> None:
    assert material["body_free"] is True
    for key in pmn.P7_R54_AHR_POST_MN11_REQUIRED_FALSE_FLAG_REFS:
        assert material[key] is False, key
    for marker_map_key in ("public_contract", "post_mn11_no_touch_contract", "body_free_markers"):
        assert material[marker_map_key]
        assert all(value is False for value in material[marker_map_key].values()), marker_map_key
    for forbidden_key in pmn.P7_R54_AHR_POST_MN11_FORBIDDEN_PAYLOAD_KEY_REFS:
        assert forbidden_key not in material, forbidden_key
    if "not_claimed_boundary" in material:
        assert all(value is False for value in material["not_claimed_boundary"].values())


def _ready_op11() -> dict[str, object]:
    return prev._ready_op11()


def _contract_fixture_sanitized_review_result_rows(op11: dict[str, object]) -> list[dict[str, object]]:
    axis_scores = {
        "history_connection_naturalness": 0.91,
        "creepy_absence": 0.96,
        "overclaim_absence": 0.96,
        "self_blame_non_amplification": 0.96,
        "wants_more_input_or_accumulation": 0.86,
        "non_shallow_repeat": 0.91,
    }
    axis_pass_flags = {
        axis: axis_scores[axis] >= pmn.P7_R54_AHR_POST_MN11_PMN_OP09_RATING_AXIS_TARGET_THRESHOLDS[axis]
        for axis in pmn.P7_R54_AHR_POST_MN11_PMN_OP09_RATING_AXIS_REFS
    }
    case_matrix = pmn.op.build_p7_r48_p5_first_formal_review_case_matrix(
        material_id="p7_r54_ahr_post_mn11_pmn_op12_op13_contract_fixture_case_matrix_basis"
    )
    pmn.op.assert_p7_r48_p5_first_formal_review_case_matrix_contract(case_matrix)

    rows: list[dict[str, object]] = []
    for index, case_row in enumerate(case_matrix["case_rows"], start=1):
        rows.append(
            {
                "schema_version": pmn.P7_R54_AHR_POST_MN11_PMN_OP12_SANITIZED_REVIEW_RESULT_ROW_SCHEMA_VERSION,
                "review_session_id": op11["review_session_id"],
                "operation_receipt_ref": op11["operation_receipt_ref"],
                "review_result_row_ref": f"postmn11_actual_review_result_row_contract_fixture_{index:03d}",
                "case_ref_id": case_row["case_ref_id"],
                "blind_case_id": case_row["blind_case_id"],
                "packet_ref_id": case_row["packet_ref_id"],
                "reviewer_person_ref": op11["reviewer_person_ref"],
                "reviewed_at_bucket_ref": op11["review_completed_at_bucket_ref"],
                "axis_scores": dict(axis_scores),
                "axis_score_count": len(pmn.P7_R54_AHR_POST_MN11_PMN_OP09_RATING_AXIS_REFS),
                "axis_pass_flags": dict(axis_pass_flags),
                "verdict_ref": "PASS",
                "label_connection_quality_ref": "label_connection_present_natural",
                "safe_display_check_refs": [
                    "no_overclaim_or_unearned_certainty",
                    "no_creepy_history_overread",
                    "no_self_blame_amplification",
                    "no_body_leak",
                    "no_question_text_leak",
                ],
                "sanitized_reason_ids": ["record_returned_as_natural_line"],
                "readfeel_blocker_ids": [],
                "execution_blocker_ids": [],
                "question_need_primary_class_ref": "no_question_needed_emlis_can_observe",
                "ambiguity_kind_refs": ["no_material_ambiguity"],
                "one_question_fit_ref": "not_needed",
                "repair_required_refs": ["no_repair_required"],
                "plan_candidate_flags": {
                    "plus_single_question_candidate_later": False,
                    "premium_deep_dive_candidate_later": False,
                    "p8_design_material_candidate_only": False,
                    "p8_implementation_spec_finalized_here": False,
                },
                "row_source_ref": pmn.P7_R54_AHR_POST_MN11_PMN_OP12_ALLOWED_ROW_SOURCE_REF,
                "row_created_by_helper": False,
                "row_created_for_unit_test": False,
                "row_is_synthetic_contract_fixture": False,
                "historical_row_reused": False,
                "selection_only": True,
                "selection_only_row": True,
                "body_free": True,
                **{flag: False for flag in pmn.P7_R54_AHR_POST_MN11_PMN_OP12_ROW_BODYFREE_FALSE_FLAG_REFS},
            }
        )
    return rows


def _ready_op12() -> dict[str, object]:
    op11 = _ready_op11()
    return pmn.build_p7_r54_ahr_post_mn11_pmn_op12_sanitized_review_result_rows_intake_provenance_guard(
        actual_operation_receipt_intake=op11,
        sanitized_review_result_rows_bodyfree=_contract_fixture_sanitized_review_result_rows(op11),
    )


def _ready_op13() -> dict[str, object]:
    return pmn.build_p7_r54_ahr_post_mn11_pmn_op13_rating_row_normalization_threshold_summary(
        sanitized_review_result_rows_intake=_ready_op12()
    )


def test_pmn_op00_to_op11_implementation_is_present_before_op12_op13() -> None:
    op11 = _ready_op11()

    assert pmn.assert_p7_r54_ahr_post_mn11_pmn_op11_actual_operation_receipt_intake_contract(op11) is True
    assert op11["next_required_step"] == pmn.P7_R54_AHR_POST_MN11_PMN_OP12_STEP_REF
    assert op11["operation_receipt_accepted"] is True
    assert op11["sanitized_review_result_rows_intake_required_next"] is True
    assert tuple(op11["implemented_steps"]) == pmn.P7_R54_AHR_POST_MN11_PMN_OP11_IMPLEMENTED_STEPS
    assert tuple(op11["not_yet_implemented_steps"]) == pmn.P7_R54_AHR_POST_MN11_PMN_OP11_NOT_YET_IMPLEMENTED_STEPS
    _assert_bodyfree_no_touch_no_promotion(op11)


def test_pmn_op12_blocks_without_sanitized_rows_and_does_not_promote() -> None:
    material = pmn.build_p7_r54_ahr_post_mn11_pmn_op12_sanitized_review_result_rows_intake_provenance_guard(
        actual_operation_receipt_intake=_ready_op11()
    )

    assert set(material) == set(pmn.P7_R54_AHR_POST_MN11_PMN_OP12_REQUIRED_FIELD_REFS)
    assert material["sanitized_review_result_rows_intake_status_ref"] == pmn.P7_R54_AHR_POST_MN11_PMN_OP12_BLOCKED_STATUS_REF
    assert material["sanitized_review_result_rows_intake_ready"] is False
    assert "pmn_op12_sanitized_review_result_rows_not_received" in material["sanitized_review_result_rows_intake_blocker_refs"]
    assert material["sanitized_review_result_rows_input_present"] is False
    assert material["sanitized_review_result_row_count"] == 0
    assert material["actual_sanitized_review_result_rows_intaken_here"] is False
    assert material["rating_row_normalization_allowed_next"] is False
    assert material["actual_review_evidence_complete_from_real_review"] is False
    assert material["next_required_step"] == pmn.P7_R54_AHR_POST_MN11_PMN_OP12_BLOCKED_NEXT_REQUIRED_STEP_REF
    assert pmn.assert_p7_r54_ahr_post_mn11_pmn_op12_sanitized_review_result_rows_intake_provenance_guard_contract(material) is True
    _assert_bodyfree_no_touch_no_promotion(material)


def test_pmn_op12_accepts_bodyfree_sanitized_rows_contract_fixture_with_provenance_guard() -> None:
    material = _ready_op12()

    assert set(material) == set(pmn.P7_R54_AHR_POST_MN11_PMN_OP12_REQUIRED_FIELD_REFS)
    assert material["schema_version"] == pmn.P7_R54_AHR_POST_MN11_PMN_OP12_SANITIZED_REVIEW_RESULT_ROWS_INTAKE_PROVENANCE_GUARD_SCHEMA_VERSION
    assert material["operation_step_ref"] == pmn.P7_R54_AHR_POST_MN11_PMN_OP12_STEP_REF
    assert material["sanitized_review_result_rows_intake_status_ref"] == pmn.P7_R54_AHR_POST_MN11_PMN_OP12_READY_STATUS_REF
    assert material["sanitized_review_result_rows_intake_ready"] is True
    assert material["sanitized_review_result_rows_intake_blocker_refs"] == []
    assert tuple(material["sanitized_review_result_rows_intake_reason_refs"]) == pmn.P7_R54_AHR_POST_MN11_PMN_OP12_READY_REASON_REFS
    assert tuple(material["sanitized_review_result_rows_required_field_refs"]) == pmn.P7_R54_AHR_POST_MN11_PMN_OP12_REQUIRED_SANITIZED_ROW_FIELD_REFS
    assert material["sanitized_review_result_rows_input_present"] is True
    assert material["received_sanitized_review_result_row_count"] == 24
    assert material["sanitized_review_result_row_count"] == 24
    assert material["sanitized_review_result_row_count_is_24"] is True
    assert len(material["review_result_rows"]) == 24
    assert material["review_result_row_ref_count"] == 24
    assert material["case_ref_id_count"] == 24
    assert material["case_ref_ids_unique"] is True
    assert material["blind_case_id_count"] == 24
    assert material["blind_case_ids_unique"] is True
    assert material["packet_ref_id_count"] == 24
    assert material["packet_ref_ids_unique"] is True
    assert material["reviewed_at_bucket_refs_present"] is True
    assert material["axis_refs"] == list(pmn.P7_R54_AHR_POST_MN11_PMN_OP09_RATING_AXIS_REFS)
    assert material["axis_ref_count"] == 6
    assert material["axis_score_count_per_row"] == 6
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
    assert material["sanitized_selection_only_result_rows_intaken_here"] is True
    assert material["actual_sanitized_review_result_rows_intaken_here"] is True
    assert material["actual_human_review_executed_by_person"] is True
    assert material["actual_selection_rows_created_here"] is False
    assert material["actual_sanitized_review_result_rows_created_here"] is False
    assert material["rating_row_normalization_allowed_next"] is True
    assert material["question_text_materialized_here"] is False
    assert material["draft_question_text_materialized_here"] is False
    assert material["p8_question_implementation_spec_finalized_here"] is False
    assert material["actual_review_evidence_complete_from_real_review"] is False
    assert material["pmn_op12_does_not_run_actual_human_review_here"] is True
    assert material["pmn_op12_does_not_create_rating_rows_question_rows_or_disposal"] is True
    assert material["pmn_op12_does_not_start_p8_p6_r52_or_release"] is True
    assert tuple(material["implemented_steps"]) == pmn.P7_R54_AHR_POST_MN11_PMN_OP12_IMPLEMENTED_STEPS
    assert tuple(material["not_yet_implemented_steps"]) == pmn.P7_R54_AHR_POST_MN11_PMN_OP12_NOT_YET_IMPLEMENTED_STEPS
    assert material["next_required_step"] == pmn.P7_R54_AHR_POST_MN11_PMN_OP13_STEP_REF
    for row in material["review_result_rows"]:
        assert row["schema_version"] == pmn.P7_R54_AHR_POST_MN11_PMN_OP12_SANITIZED_REVIEW_RESULT_ROW_SCHEMA_VERSION
        assert row["row_source_ref"] == pmn.P7_R54_AHR_POST_MN11_PMN_OP12_ALLOWED_ROW_SOURCE_REF
        assert row["row_created_by_helper"] is False
        assert row["row_created_for_unit_test"] is False
        assert row["row_is_synthetic_contract_fixture"] is False
        assert row["historical_row_reused"] is False
        assert row["selection_only"] is True
        assert row["selection_only_row"] is True
        assert row["body_free"] is True
        for false_flag in pmn.P7_R54_AHR_POST_MN11_PMN_OP12_ROW_BODYFREE_FALSE_FLAG_REFS:
            assert row[false_flag] is False
    assert pmn.assert_p7_r54_ahr_post_mn11_pmn_op12_sanitized_review_result_rows_intake_provenance_guard_contract(material) is True
    _assert_bodyfree_no_touch_no_promotion(material)


@pytest.mark.parametrize(
    ("field", "bad_value"),
    [
        ("sanitized_review_result_rows_intake_ready", False),
        ("sanitized_review_result_row_count", 23),
        ("rows_match_24_case_manifest", False),
        ("rows_bodyfree_only", False),
        ("rows_selection_only", False),
        ("rows_have_actual_person_selection_only_provenance", False),
        ("rows_have_no_body_or_question_or_path_or_hash", False),
        ("actual_sanitized_review_result_rows_intaken_here", False),
        ("actual_selection_rows_created_here", True),
        ("actual_sanitized_review_result_rows_created_here", True),
        ("rating_row_normalization_allowed_next", False),
        ("question_text_materialized_here", True),
        ("draft_question_text_materialized_here", True),
        ("p8_question_implementation_spec_finalized_here", True),
        ("actual_review_evidence_complete_from_real_review", True),
        ("p8_start_allowed", True),
    ],
)
def test_pmn_op12_contract_rejects_rows_leak_creation_or_promotion_mutation(field: str, bad_value: object) -> None:
    material = _ready_op12()
    mutated = deepcopy(material)
    mutated[field] = bad_value

    with pytest.raises(ValueError):
        pmn.assert_p7_r54_ahr_post_mn11_pmn_op12_sanitized_review_result_rows_intake_provenance_guard_contract(mutated)


@pytest.mark.parametrize(
    ("field", "bad_value", "expected_blocker"),
    [
        ("row_source_ref", "unit_test_contract_rows", "pmn_op12_sanitized_row_source_ref_not_actual_person_selection_only_rows_local_review"),
        ("row_created_by_helper", True, "pmn_op12_sanitized_row_created_by_helper_cannot_be_actual"),
        ("row_created_for_unit_test", True, "pmn_op12_sanitized_row_created_for_unit_test_cannot_be_actual"),
        ("row_is_synthetic_contract_fixture", True, "pmn_op12_sanitized_row_is_synthetic_contract_fixture_cannot_be_actual"),
        ("historical_row_reused", True, "pmn_op12_sanitized_row_historical_row_reused_cannot_be_actual"),
        ("reviewer_person_ref", "different_reviewer_ref", "pmn_op12_sanitized_row_reviewer_person_ref_mismatch"),
        ("case_ref_id", "wrong_case_ref", "pmn_op12_sanitized_row_manifest_id_mismatch"),
        ("operation_receipt_ref", "different_operation_receipt_ref", "pmn_op12_sanitized_row_operation_receipt_ref_mismatch"),
        ("selection_only", False, "pmn_op12_sanitized_row_selection_only_not_true"),
        ("question_text_included", True, "pmn_op12_sanitized_row_bodyfree_false_flag_not_false"),
        ("body_hash_included", True, "pmn_op12_sanitized_row_bodyfree_false_flag_not_false"),
        ("verdict_ref", "UNKNOWN", "pmn_op12_sanitized_row_allowed_option_ref_invalid"),
    ],
)
def test_pmn_op12_blocks_rows_with_invalid_source_manifest_leak_or_fixture_source(
    field: str, bad_value: object, expected_blocker: str
) -> None:
    op11 = _ready_op11()
    rows = _contract_fixture_sanitized_review_result_rows(op11)
    rows[0][field] = bad_value

    material = pmn.build_p7_r54_ahr_post_mn11_pmn_op12_sanitized_review_result_rows_intake_provenance_guard(
        actual_operation_receipt_intake=op11,
        sanitized_review_result_rows_bodyfree=rows,
    )

    assert material["sanitized_review_result_rows_intake_ready"] is False
    assert expected_blocker in material["sanitized_review_result_rows_intake_blocker_refs"]
    assert material["rating_row_normalization_allowed_next"] is False
    assert material["next_required_step"] == pmn.P7_R54_AHR_POST_MN11_PMN_OP12_BLOCKED_NEXT_REQUIRED_STEP_REF
    assert pmn.assert_p7_r54_ahr_post_mn11_pmn_op12_sanitized_review_result_rows_intake_provenance_guard_contract(material) is True
    _assert_bodyfree_no_touch_no_promotion(material)


def test_pmn_op12_blocks_rows_with_axis_score_out_of_range() -> None:
    op11 = _ready_op11()
    rows = _contract_fixture_sanitized_review_result_rows(op11)
    rows[0]["axis_scores"] = dict(rows[0]["axis_scores"])
    rows[0]["axis_scores"]["creepy_absence"] = 1.5

    material = pmn.build_p7_r54_ahr_post_mn11_pmn_op12_sanitized_review_result_rows_intake_provenance_guard(
        actual_operation_receipt_intake=op11,
        sanitized_review_result_rows_bodyfree=rows,
    )

    assert material["sanitized_review_result_rows_intake_ready"] is False
    assert "pmn_op12_sanitized_row_axis_scores_missing_or_out_of_range" in material["sanitized_review_result_rows_intake_blocker_refs"]
    assert pmn.assert_p7_r54_ahr_post_mn11_pmn_op12_sanitized_review_result_rows_intake_provenance_guard_contract(material) is True
    _assert_bodyfree_no_touch_no_promotion(material)


def test_pmn_op12_blocks_rows_with_forbidden_payload_key() -> None:
    op11 = _ready_op11()
    rows = _contract_fixture_sanitized_review_result_rows(op11)
    rows[0]["question_text"] = "forbidden"

    material = pmn.build_p7_r54_ahr_post_mn11_pmn_op12_sanitized_review_result_rows_intake_provenance_guard(
        actual_operation_receipt_intake=op11,
        sanitized_review_result_rows_bodyfree=rows,
    )

    assert material["sanitized_review_result_rows_intake_ready"] is False
    assert material["sanitized_review_result_rows_intake_status_ref"] == pmn.P7_R54_AHR_POST_MN11_PMN_OP12_BLOCKED_BY_LEAK_STATUS_REF
    assert "pmn_op12_sanitized_row_contains_forbidden_body_question_path_hash_or_terminal_key" in material["sanitized_review_result_rows_intake_blocker_refs"]
    assert pmn.assert_p7_r54_ahr_post_mn11_pmn_op12_sanitized_review_result_rows_intake_provenance_guard_contract(material) is True
    _assert_bodyfree_no_touch_no_promotion(material)


def test_pmn_op13_blocks_until_op12_ready() -> None:
    material = pmn.build_p7_r54_ahr_post_mn11_pmn_op13_rating_row_normalization_threshold_summary(
        sanitized_review_result_rows_intake=pmn.build_p7_r54_ahr_post_mn11_pmn_op12_sanitized_review_result_rows_intake_provenance_guard(
            actual_operation_receipt_intake=_ready_op11()
        )
    )

    assert set(material) == set(pmn.P7_R54_AHR_POST_MN11_PMN_OP13_REQUIRED_FIELD_REFS)
    assert material["rating_row_normalization_status_ref"] == pmn.P7_R54_AHR_POST_MN11_PMN_OP13_BLOCKED_STATUS_REF
    assert material["rating_row_normalization_ready"] is False
    assert "pmn_op13_op12_sanitized_review_result_rows_not_ready" in material["rating_row_normalization_blocker_refs"]
    assert material["rating_row_count"] == 0
    assert material["actual_rating_rows_materialized_from_actual_rows"] is False
    assert material["rating_rows_normalized_here"] is False
    assert material["question_need_observation_row_normalization_allowed_next"] is False
    assert material["p5_final_allowed"] is False
    assert material["next_required_step"] == pmn.P7_R54_AHR_POST_MN11_PMN_OP13_BLOCKED_NEXT_REQUIRED_STEP_REF
    assert pmn.assert_p7_r54_ahr_post_mn11_pmn_op13_rating_row_normalization_threshold_summary_contract(material) is True
    _assert_bodyfree_no_touch_no_promotion(material)


def test_pmn_op13_normalizes_rating_rows_from_accepted_sanitized_rows_without_p5_final() -> None:
    material = _ready_op13()

    assert set(material) == set(pmn.P7_R54_AHR_POST_MN11_PMN_OP13_REQUIRED_FIELD_REFS)
    assert material["schema_version"] == pmn.P7_R54_AHR_POST_MN11_PMN_OP13_RATING_ROW_NORMALIZATION_THRESHOLD_SUMMARY_SCHEMA_VERSION
    assert material["operation_step_ref"] == pmn.P7_R54_AHR_POST_MN11_PMN_OP13_STEP_REF
    assert material["rating_row_normalization_status_ref"] == pmn.P7_R54_AHR_POST_MN11_PMN_OP13_READY_STATUS_REF
    assert material["rating_row_normalization_ready"] is True
    assert material["rating_row_normalization_blocker_refs"] == []
    assert tuple(material["rating_row_normalization_reason_refs"]) == pmn.P7_R54_AHR_POST_MN11_PMN_OP13_READY_REASON_REFS
    assert tuple(material["rating_row_required_field_refs"]) == pmn.P7_R54_AHR_POST_MN11_PMN_OP13_REQUIRED_RATING_ROW_FIELD_REFS
    assert material["op12_sanitized_rows_ready"] is True
    assert material["op12_sanitized_review_result_row_count"] == 24
    assert material["rating_row_count"] == 24
    assert material["rating_row_count_is_24"] is True
    assert len(material["rating_rows"]) == 24
    assert material["rating_row_ref_count"] == 24
    assert material["axis_refs"] == list(pmn.P7_R54_AHR_POST_MN11_PMN_OP09_RATING_AXIS_REFS)
    assert material["axis_ref_count"] == 6
    assert material["axis_score_count_per_row"] == 6
    assert material["axis_target_thresholds_present"] is True
    assert material["below_target_axis_refs"] == []
    assert material["below_target_axis_ref_count"] == 0
    assert material["all_axis_target_passed"] is True
    assert material["verdict_distribution_ref"] == {"PASS": 24}
    assert material["label_connection_distribution_ref"] == {"label_connection_present_natural": 24}
    assert material["actual_rating_rows_materialized_from_actual_rows"] is True
    assert material["rating_rows_normalized_here"] is True
    assert material["rating_decision_material_only"] is True
    assert material["p5_final_allowed"] is False
    assert material["p5_finalization_still_manual_decision_required"] is True
    assert material["question_need_observation_row_normalization_allowed_next"] is True
    assert material["actual_review_evidence_complete_from_real_review"] is False
    assert material["actual_review_evidence_complete_from_real_review_still_false"] is True
    assert material["pmn_op13_does_not_create_question_rows_or_disposal"] is True
    assert material["pmn_op13_does_not_start_p5_p6_p8_r52_or_release"] is True
    assert tuple(material["implemented_steps"]) == pmn.P7_R54_AHR_POST_MN11_PMN_OP13_IMPLEMENTED_STEPS
    assert tuple(material["not_yet_implemented_steps"]) == pmn.P7_R54_AHR_POST_MN11_PMN_OP13_NOT_YET_IMPLEMENTED_STEPS
    assert material["next_required_step"] == pmn.P7_R54_AHR_POST_MN11_PMN_OP14_STEP_REF
    for row in material["rating_rows"]:
        assert row["schema_version"] == pmn.P7_R54_AHR_POST_MN11_PMN_OP13_RATING_ROW_SCHEMA_VERSION
        assert row["row_source_ref"] == pmn.P7_R54_AHR_POST_MN11_PMN_OP12_ALLOWED_ROW_SOURCE_REF
        assert row["rating_decision_material_only"] is True
        assert row["body_free"] is True
        assert row["below_target_axis_refs"] == []
        assert row["all_axis_target_passed"] is True
    assert pmn.assert_p7_r54_ahr_post_mn11_pmn_op13_rating_row_normalization_threshold_summary_contract(material) is True
    _assert_bodyfree_no_touch_no_promotion(material)


@pytest.mark.parametrize(
    ("field", "bad_value"),
    [
        ("rating_row_normalization_ready", False),
        ("rating_row_count", 23),
        ("actual_rating_rows_materialized_from_actual_rows", False),
        ("rating_rows_normalized_here", False),
        ("rating_decision_material_only", False),
        ("p5_final_allowed", True),
        ("question_need_observation_row_normalization_allowed_next", False),
        ("actual_rating_rows_materialized_here", True),
        ("actual_question_need_observation_rows_materialized_here", True),
        ("actual_disposal_receipt_materialized_here", True),
        ("actual_review_evidence_complete_from_real_review", True),
        ("p8_start_allowed", True),
    ],
)
def test_pmn_op13_contract_rejects_rating_rows_creation_or_promotion_mutation(field: str, bad_value: object) -> None:
    material = _ready_op13()
    mutated = deepcopy(material)
    mutated[field] = bad_value

    with pytest.raises(ValueError):
        pmn.assert_p7_r54_ahr_post_mn11_pmn_op13_rating_row_normalization_threshold_summary_contract(mutated)


def test_pmn_op13_blocks_if_op12_next_step_or_allowed_next_is_mutated() -> None:
    op12 = _ready_op12()
    mutated_op12 = deepcopy(op12)
    mutated_op12["rating_row_normalization_allowed_next"] = False

    material = pmn.build_p7_r54_ahr_post_mn11_pmn_op13_rating_row_normalization_threshold_summary(
        sanitized_review_result_rows_intake=mutated_op12
    )

    assert material["rating_row_normalization_ready"] is False
    assert "pmn_op13_op12_sanitized_review_result_rows_intake_invalid" in material["rating_row_normalization_blocker_refs"]
    assert "pmn_op13_op12_rating_row_normalization_not_allowed_next" in material["rating_row_normalization_blocker_refs"]
    assert material["next_required_step"] == pmn.P7_R54_AHR_POST_MN11_PMN_OP13_BLOCKED_NEXT_REQUIRED_STEP_REF
    assert pmn.assert_p7_r54_ahr_post_mn11_pmn_op13_rating_row_normalization_threshold_summary_contract(material) is True
    _assert_bodyfree_no_touch_no_promotion(material)


def test_pmn_op12_op13_aliases_match_primary_builders_and_contracts() -> None:
    op11 = _ready_op11()
    rows = _contract_fixture_sanitized_review_result_rows(op11)
    primary_op12 = pmn.build_p7_r54_ahr_post_mn11_pmn_op12_sanitized_review_result_rows_intake_provenance_guard(
        actual_operation_receipt_intake=op11,
        sanitized_review_result_rows_bodyfree=rows,
    )
    alias_op12 = pmn.build_p7_r54_ahr_post_mn11_actual_operation_sanitized_review_result_rows_intake_provenance_guard_bodyfree(
        actual_operation_receipt_intake=op11,
        sanitized_review_result_rows_bodyfree=rows,
    )
    assert alias_op12 == primary_op12
    assert pmn.assert_p7_r54_ahr_post_mn11_actual_operation_sanitized_review_result_rows_intake_provenance_guard_bodyfree_contract(alias_op12) is True

    primary_op13 = pmn.build_p7_r54_ahr_post_mn11_pmn_op13_rating_row_normalization_threshold_summary(
        sanitized_review_result_rows_intake=primary_op12
    )
    alias_op13 = pmn.build_p7_r54_ahr_post_mn11_actual_operation_rating_row_normalization_threshold_summary_bodyfree(
        sanitized_review_result_rows_intake=primary_op12
    )
    assert alias_op13 == primary_op13
    assert pmn.assert_p7_r54_ahr_post_mn11_actual_operation_rating_row_normalization_threshold_summary_bodyfree_contract(alias_op13) is True
