# -*- coding: utf-8 -*-
"""R54-AHR Post-ALR12 explicit local-only review start/retry ELR-OP12/OP13 tests."""

from __future__ import annotations

from copy import deepcopy
from pathlib import Path
import sys

import pytest

TEST_DIR = Path(__file__).resolve().parent
if str(TEST_DIR) not in sys.path:
    sys.path.insert(0, str(TEST_DIR))

import emlis_ai_p7_r54_ahr_post_alr12_explicit_local_only_review_start_retry_operation_20260703 as elr
from test_r54_ahr_post_alr12_explicit_local_only_review_start_retry_operation_elr_op06_op07_20260703 import (  # noqa: E501
    _assert_common_bodyfree_no_touch_no_promotion,
)
from test_r54_ahr_post_alr12_explicit_local_only_review_start_retry_operation_elr_op10_op11_20260703 import (  # noqa: E501
    _case_refs,
    _op10_accepted,
    _valid_sanitized_rows,
)

_OP11_NORMALIZED_CACHE: dict[str, object] | None = None
_OP12_NORMALIZED_CACHE: dict[str, object] | None = None


def _op10_from_rows(rows: list[dict[str, object]]) -> dict[str, object]:
    from test_r54_ahr_post_alr12_explicit_local_only_review_start_retry_operation_elr_op10_op11_20260703 import (  # noqa: E501
        _op09_accepted,
    )

    material = elr.build_p7_r54_ahr_post_alr12_elr_op10_sanitized_review_result_rows_intake_provenance_guard(
        actual_operation_receipt_intake=_op09_accepted(),
        sanitized_review_result_rows_optional=rows,
        expected_case_refs=_case_refs(),
    )
    assert material["sanitized_rows_status_ref"] == elr.P7_R54_AHR_POST_ALR12_ELR_OP10_STATUS_ACCEPTED_BODYFREE_REF
    assert elr.assert_p7_r54_ahr_post_alr12_elr_op10_sanitized_review_result_rows_intake_provenance_guard_contract(material) is True
    return material


def _op11_from_op10(op10: dict[str, object]) -> dict[str, object]:
    material = elr.build_p7_r54_ahr_post_alr12_elr_op11_rating_rows_normalization_threshold_summary(
        op10_sanitized_review_result_rows_intake=op10,
    )
    assert material["rating_rows_status_ref"] == elr.P7_R54_AHR_POST_ALR12_ELR_OP11_STATUS_NORMALIZED_BODYFREE_REF
    assert elr.assert_p7_r54_ahr_post_alr12_elr_op11_rating_rows_normalization_threshold_summary_contract(material) is True
    return material


def _op11_normalized() -> dict[str, object]:
    global _OP11_NORMALIZED_CACHE
    if _OP11_NORMALIZED_CACHE is None:
        _OP11_NORMALIZED_CACHE = _op11_from_op10(_op10_accepted())
    return deepcopy(_OP11_NORMALIZED_CACHE)


def _valid_question_need_rows(
    op10: dict[str, object] | None = None,
    op11: dict[str, object] | None = None,
) -> list[dict[str, object]]:
    op10 = op10 or _op10_accepted()
    op11 = op11 or _op11_normalized()
    rating_rows_by_case = {str(row["case_ref"]): row for row in op11["rating_rows"]}
    rows: list[dict[str, object]] = []
    for index, review_row in enumerate(op10["review_result_rows"], start=1):
        case_ref = str(review_row["case_ref"])
        rating_row = rating_rows_by_case[case_ref]
        primary_class = str(review_row["question_need_primary_class_ref"])
        rows.append(
            {
                "schema_version": elr.P7_R54_AHR_POST_ALR12_ELR_QUESTION_NEED_OBSERVATION_ROW_SCHEMA_VERSION,
                "question_need_observation_row_ref": f"elr_op12_question_need_observation_row_{index:03d}_bodyfree",
                "source_sanitized_review_result_row_ref": str(review_row["review_result_row_ref"]),
                "source_rating_row_ref": str(rating_row["rating_row_ref"]),
                "review_session_id": str(op11["review_session_id"]),
                "operation_receipt_ref": str(op11["operation_receipt_ref"]),
                "case_ref": case_ref,
                "reviewer_person_ref": str(op11["reviewer_person_ref"]),
                "source_kind_ref": elr.P7_R54_AHR_POST_ALR12_ELR_ACTUAL_REVIEW_SOURCE_KIND_REF,
                "question_need_primary_class_ref": primary_class,
                "ambiguity_kind_refs": list(review_row["ambiguity_kind_refs"]),
                "one_question_fit_ref": str(review_row["one_question_fit_ref"]),
                "repair_required_refs": list(review_row["repair_required_refs"]),
                "selection_only": True,
                "actual_question_need_observation_row_from_real_operation": True,
                "question_observation_material_only": True,
                "p8_design_material_candidate_only": primary_class in elr.P7_R54_AHR_POST_ALR12_ELR_P8_DESIGN_MATERIAL_CANDIDATE_QUESTION_CLASS_REFS,
                **{field: False for field in elr.P7_R54_AHR_POST_ALR12_ELR_OP12_ROW_BODYFREE_FALSE_FIELD_REFS},
                "body_free": True,
            }
        )
    return rows


def _op12_normalized() -> dict[str, object]:
    global _OP12_NORMALIZED_CACHE
    if _OP12_NORMALIZED_CACHE is None:
        op10 = _op10_accepted()
        op11 = _op11_normalized()
        material = elr.build_p7_r54_ahr_post_alr12_elr_op12_question_need_observation_rows_normalization(
            op11_rating_rows_normalization=op11,
            question_need_observation_rows=_valid_question_need_rows(op10, op11),
        )
        assert material["question_need_rows_status_ref"] == elr.P7_R54_AHR_POST_ALR12_ELR_OP12_STATUS_NORMALIZED_BODYFREE_REF
        assert elr.assert_p7_r54_ahr_post_alr12_elr_op12_question_need_observation_rows_normalization_contract(material) is True
        _OP12_NORMALIZED_CACHE = material
    return deepcopy(_OP12_NORMALIZED_CACHE)


def test_elr_op12_missing_question_need_rows_waits_after_op11_without_p8_or_complete_claim() -> None:
    op11 = _op11_normalized()
    material = elr.build_p7_r54_ahr_post_alr12_elr_op12_question_need_observation_rows_normalization(
        op11_rating_rows_normalization=op11,
    )

    assert set(material) == set(elr.P7_R54_AHR_POST_ALR12_ELR_OP12_REQUIRED_FIELD_REFS)
    assert material["schema_version"] == elr.P7_R54_AHR_POST_ALR12_ELR_OP12_SCHEMA_VERSION
    assert material["op11_rating_rows_normalized"] is True
    assert material["question_need_rows_status_ref"] == elr.P7_R54_AHR_POST_ALR12_ELR_OP12_STATUS_MISSING_WAITING_REF
    assert material["question_need_observation_rows_missing_waiting"] is True
    assert material["ready_for_rating_question_consistency"] is False
    assert material["question_need_observation_row_count"] == 0
    assert material["p8_question_spec_created_here"] is False
    assert material["actual_review_evidence_complete_here"] is False
    assert material["next_required_step"] == elr.P7_R54_AHR_POST_ALR12_ELR_NEXT_STEP_PROVIDE_QUESTION_NEED_OBSERVATION_ROWS_REF
    assert elr.assert_p7_r54_ahr_post_alr12_elr_op12_question_need_observation_rows_normalization_contract(material) is True
    _assert_common_bodyfree_no_touch_no_promotion(material)


def test_elr_op12_normalizes_24_bodyfree_question_observation_rows_without_question_text_or_p8_spec() -> None:
    material = _op12_normalized()

    assert set(material) == set(elr.P7_R54_AHR_POST_ALR12_ELR_OP12_REQUIRED_FIELD_REFS)
    assert material["question_need_rows_status_ref"] == elr.P7_R54_AHR_POST_ALR12_ELR_OP12_STATUS_NORMALIZED_BODYFREE_REF
    assert material["question_need_observation_rows_normalized"] is True
    assert material["question_need_observation_row_count"] == 24
    assert material["question_need_observation_row_count_is_24"] is True
    assert material["case_refs_unique"] is True
    assert material["case_refs_match_rating_rows"] is True
    assert material["source_rating_row_refs_match_rating_rows"] is True
    assert material["question_need_rows_bodyfree_only"] is True
    assert material["question_need_rows_selection_only"] is True
    assert material["question_need_rows_from_actual_review_rows"] is True
    assert material["question_need_rows_have_no_text_body_path_hash"] is True
    assert material["question_need_row_provenance_guard_passed"] is True
    assert material["p8_question_spec_created_here"] is False
    assert material["question_text_materialized_here"] is False
    assert material["actual_question_need_observation_rows_created_here_by_helper"] is False
    assert material["actual_review_evidence_complete_here"] is False
    assert material["next_required_step"] == elr.P7_R54_AHR_POST_ALR12_ELR_OP13_STEP_REF
    assert material["elr_op12_blocker_refs"] == []
    assert elr.assert_p7_r54_ahr_post_alr12_elr_op12_question_need_observation_rows_normalization_contract(material) is True
    _assert_common_bodyfree_no_touch_no_promotion(material)


def test_elr_op12_keeps_p8_question_candidates_as_design_material_only() -> None:
    rows = _valid_sanitized_rows()
    rows[0]["question_need_primary_class_ref"] = "plus_single_question_candidate_later"
    rows[0]["one_question_fit_ref"] = "fits_one_question"
    rows[1]["question_need_primary_class_ref"] = "premium_deep_dive_candidate_later"
    rows[1]["one_question_fit_ref"] = "needs_more_than_one_question_not_p7"
    op10 = _op10_from_rows(rows)
    op11 = _op11_from_op10(op10)
    question_rows = _valid_question_need_rows(op10, op11)
    material = elr.build_p7_r54_ahr_post_alr12_elr_op12_question_need_observation_rows_normalization(
        op11_rating_rows_normalization=op11,
        question_need_observation_rows=question_rows,
    )

    assert material["question_need_rows_status_ref"] == elr.P7_R54_AHR_POST_ALR12_ELR_OP12_STATUS_NORMALIZED_BODYFREE_REF
    assert material["p8_design_material_candidate_case_ref_count"] == 2
    assert material["p8_design_material_candidate_case_refs"] == [
        "elr_op04_case_ref_001_bodyfree",
        "elr_op04_case_ref_002_bodyfree",
    ]
    assert material["p8_question_spec_created_here"] is False
    assert material["p8_start_allowed"] is False
    assert material["next_required_step"] == elr.P7_R54_AHR_POST_ALR12_ELR_OP13_STEP_REF
    assert elr.assert_p7_r54_ahr_post_alr12_elr_op12_question_need_observation_rows_normalization_contract(material) is True


@pytest.mark.parametrize(
    ("field", "bad_value", "expected_blocker"),
    [
        ("source_kind_ref", "helper_generated_question_rows", "elr_op12_question_need_row_source_kind_not_actual_local_only_human_review_by_person"),
        ("row_created_by_helper", True, "elr_op12_row_created_by_helper_mismatch"),
        ("question_text_included", True, "elr_op12_question_text_included_mismatch"),
        ("question_text_materialized", True, "elr_op12_question_text_materialized_mismatch"),
        ("p8_question_spec_created", True, "elr_op12_p8_question_spec_created_mismatch"),
        ("question_need_primary_class_ref", "p8_question_text_ready", "elr_op12_question_need_primary_class_ref_not_allowed"),
        ("one_question_fit_ref", "ask_now", "elr_op12_one_question_fit_ref_not_allowed"),
        ("body_free", False, "elr_op12_question_need_row_body_free_not_true"),
    ],
)
def test_elr_op12_rejects_invalid_question_rows_or_p8_materialization(
    field: str, bad_value: object, expected_blocker: str
) -> None:
    op10 = _op10_accepted()
    op11 = _op11_normalized()
    rows = _valid_question_need_rows(op10, op11)
    rows[0][field] = bad_value
    material = elr.build_p7_r54_ahr_post_alr12_elr_op12_question_need_observation_rows_normalization(
        op11_rating_rows_normalization=op11,
        question_need_observation_rows=rows,
    )

    assert material["question_need_rows_status_ref"] == elr.P7_R54_AHR_POST_ALR12_ELR_OP12_STATUS_INVALID_OR_REPAIR_REQUIRED_REF
    assert expected_blocker in material["elr_op12_blocker_refs"]
    assert material["question_need_observation_rows_normalized"] is False
    assert material["ready_for_rating_question_consistency"] is False
    assert material["next_required_step"] == elr.P7_R54_AHR_POST_ALR12_ELR_NEXT_STEP_REPAIR_QUESTION_NEED_OBSERVATION_ROWS_REF
    assert elr.assert_p7_r54_ahr_post_alr12_elr_op12_question_need_observation_rows_normalization_contract(material) is True


def test_elr_op12_rejects_forbidden_payload_key_without_leaking_body_value() -> None:
    op10 = _op10_accepted()
    op11 = _op11_normalized()
    rows = _valid_question_need_rows(op10, op11)
    rows[0]["question_text"] = "body-full question text must never leak"
    material = elr.build_p7_r54_ahr_post_alr12_elr_op12_question_need_observation_rows_normalization(
        op11_rating_rows_normalization=op11,
        question_need_observation_rows=rows,
    )

    assert material["question_need_rows_status_ref"] == elr.P7_R54_AHR_POST_ALR12_ELR_OP12_STATUS_INVALID_OR_REPAIR_REQUIRED_REF
    assert material["question_need_rows_forbidden_payload_key_paths"] == ["question_need_observation_rows[0].question_text"]
    assert "body-full question text must never leak" not in repr(material)
    assert "elr_op12_question_need_rows_forbidden_payload_key_detected" in material["elr_op12_blocker_refs"]
    assert elr.assert_p7_r54_ahr_post_alr12_elr_op12_question_need_observation_rows_normalization_contract(material) is True


def test_elr_op12_rejects_incomplete_rows_and_rating_source_mismatch() -> None:
    op10 = _op10_accepted()
    op11 = _op11_normalized()
    incomplete = _valid_question_need_rows(op10, op11)[:-1]
    missing = elr.build_p7_r54_ahr_post_alr12_elr_op12_question_need_observation_rows_normalization(
        op11_rating_rows_normalization=op11,
        question_need_observation_rows=incomplete,
    )
    assert missing["question_need_rows_status_ref"] == elr.P7_R54_AHR_POST_ALR12_ELR_OP12_STATUS_INVALID_OR_REPAIR_REQUIRED_REF
    assert "elr_op12_question_need_observation_row_count_not_24" in missing["elr_op12_blocker_refs"]

    mismatched = _valid_question_need_rows(op10, op11)
    mismatched[0]["source_rating_row_ref"] = "elr_op11_rating_row_unmatched_bodyfree"
    material = elr.build_p7_r54_ahr_post_alr12_elr_op12_question_need_observation_rows_normalization(
        op11_rating_rows_normalization=op11,
        question_need_observation_rows=mismatched,
    )
    assert material["question_need_rows_status_ref"] == elr.P7_R54_AHR_POST_ALR12_ELR_OP12_STATUS_INVALID_OR_REPAIR_REQUIRED_REF
    assert "elr_op12_source_rating_row_ref_mismatch" in material["elr_op12_blocker_refs"]
    assert "elr_op12_source_rating_row_refs_do_not_match_rating_rows" in material["elr_op12_blocker_refs"]
    assert elr.assert_p7_r54_ahr_post_alr12_elr_op12_question_need_observation_rows_normalization_contract(material) is True


@pytest.mark.parametrize(
    ("field", "bad_value"),
    [
        ("question_need_observation_rows_normalized", False),
        ("question_need_observation_row_count", 23),
        ("p8_question_spec_created_here", True),
        ("question_text_materialized_here", True),
        ("actual_review_evidence_complete_here", True),
        ("p8_start_allowed", True),
    ],
)
def test_elr_op12_contract_rejects_normalized_mutations(field: str, bad_value: object) -> None:
    material = _op12_normalized()
    material[field] = bad_value

    with pytest.raises(ValueError):
        elr.assert_p7_r54_ahr_post_alr12_elr_op12_question_need_observation_rows_normalization_contract(material)


def test_elr_op13_waits_when_op12_question_rows_are_missing() -> None:
    op11 = _op11_normalized()
    op12_missing = elr.build_p7_r54_ahr_post_alr12_elr_op12_question_need_observation_rows_normalization(
        op11_rating_rows_normalization=op11,
    )
    material = elr.build_p7_r54_ahr_post_alr12_elr_op13_rating_question_consistency_blocker_separation(
        op11_rating_rows_normalization=op11,
        op12_question_need_observation_rows_normalization=op12_missing,
    )

    assert set(material) == set(elr.P7_R54_AHR_POST_ALR12_ELR_OP13_REQUIRED_FIELD_REFS)
    assert material["rating_question_consistency_status_ref"] == elr.P7_R54_AHR_POST_ALR12_ELR_OP13_STATUS_WAITING_REF
    assert material["rating_question_consistency_waiting"] is True
    assert material["ready_for_disposal_purge_receipt_intake"] is False
    assert material["actual_review_evidence_complete_here"] is False
    assert material["next_required_step"] == elr.P7_R54_AHR_POST_ALR12_ELR_NEXT_STEP_PROVIDE_QUESTION_NEED_OBSERVATION_ROWS_REF
    assert elr.assert_p7_r54_ahr_post_alr12_elr_op13_rating_question_consistency_blocker_separation_contract(material) is True
    _assert_common_bodyfree_no_touch_no_promotion(material)


def test_elr_op13_passes_rating_question_consistency_and_routes_only_to_purge_receipt() -> None:
    op11 = _op11_normalized()
    op12 = _op12_normalized()
    material = elr.build_p7_r54_ahr_post_alr12_elr_op13_rating_question_consistency_blocker_separation(
        op11_rating_rows_normalization=op11,
        op12_question_need_observation_rows_normalization=op12,
    )

    assert set(material) == set(elr.P7_R54_AHR_POST_ALR12_ELR_OP13_REQUIRED_FIELD_REFS)
    assert material["rating_question_consistency_status_ref"] == elr.P7_R54_AHR_POST_ALR12_ELR_OP13_STATUS_PASSED_REF
    assert material["rating_question_consistency_passed"] is True
    assert material["ready_for_disposal_purge_receipt_intake"] is True
    assert material["rating_question_case_ref_sets_match"] is True
    assert material["rating_question_case_ref_count_is_24"] is True
    assert material["p8_question_material_candidates_are_bodyfree_refs_only"] is True
    assert material["p8_start_allowed_here"] is False
    assert material["p8_question_implementation_allowed"] is False
    assert material["actual_review_evidence_complete_here"] is False
    assert material["next_required_step"] == elr.P7_R54_AHR_POST_ALR12_ELR_OP14_STEP_REF
    assert material["elr_op13_blocker_refs"] == []
    assert elr.assert_p7_r54_ahr_post_alr12_elr_op13_rating_question_consistency_blocker_separation_contract(material) is True
    _assert_common_bodyfree_no_touch_no_promotion(material)


def test_elr_op13_separates_low_rating_question_candidate_without_auto_p8() -> None:
    rows = _valid_sanitized_rows(
        score_overrides_by_index={1: {"history_connection_naturalness": 0.25}},
    )
    rows[0]["question_need_primary_class_ref"] = "plus_single_question_candidate_later"
    rows[0]["one_question_fit_ref"] = "fits_one_question"
    op10 = _op10_from_rows(rows)
    op11 = _op11_from_op10(op10)
    op12 = elr.build_p7_r54_ahr_post_alr12_elr_op12_question_need_observation_rows_normalization(
        op11_rating_rows_normalization=op11,
        question_need_observation_rows=_valid_question_need_rows(op10, op11),
    )
    assert elr.assert_p7_r54_ahr_post_alr12_elr_op12_question_need_observation_rows_normalization_contract(op12) is True

    material = elr.build_p7_r54_ahr_post_alr12_elr_op13_rating_question_consistency_blocker_separation(
        op11_rating_rows_normalization=op11,
        op12_question_need_observation_rows_normalization=op12,
    )

    assert material["rating_question_consistency_status_ref"] == elr.P7_R54_AHR_POST_ALR12_ELR_OP13_STATUS_PASSED_REF
    assert material["low_rating_with_question_candidate_case_refs"] == ["elr_op04_case_ref_001_bodyfree"]
    assert material["question_candidate_case_refs"] == ["elr_op04_case_ref_001_bodyfree"]
    assert material["p8_design_material_candidate_only"] is True
    assert material["p8_start_allowed_here"] is False
    assert material["p8_question_implementation_allowed"] is False
    assert material["next_required_step"] == elr.P7_R54_AHR_POST_ALR12_ELR_OP14_STEP_REF
    assert elr.assert_p7_r54_ahr_post_alr12_elr_op13_rating_question_consistency_blocker_separation_contract(material) is True


def test_elr_op13_separates_not_question_repair_and_execution_blocker_classes() -> None:
    rows = _valid_sanitized_rows()
    rows[0]["question_need_primary_class_ref"] = "not_question_emlis_readfeel_repair_required"
    rows[0]["one_question_fit_ref"] = "repair_required_not_question"
    rows[1]["question_need_primary_class_ref"] = "not_question_p5_surface_repair_required"
    rows[1]["one_question_fit_ref"] = "repair_required_not_question"
    rows[2]["question_need_primary_class_ref"] = "not_question_gate_boundary_required"
    rows[2]["one_question_fit_ref"] = "unsafe_or_boundary_not_question"
    rows[3]["question_need_primary_class_ref"] = "insufficient_material_execution_blocker"
    rows[3]["one_question_fit_ref"] = "insufficient_material"
    op10 = _op10_from_rows(rows)
    op11 = _op11_from_op10(op10)
    op12 = elr.build_p7_r54_ahr_post_alr12_elr_op12_question_need_observation_rows_normalization(
        op11_rating_rows_normalization=op11,
        question_need_observation_rows=_valid_question_need_rows(op10, op11),
    )
    assert elr.assert_p7_r54_ahr_post_alr12_elr_op12_question_need_observation_rows_normalization_contract(op12) is True

    material = elr.build_p7_r54_ahr_post_alr12_elr_op13_rating_question_consistency_blocker_separation(
        op11_rating_rows_normalization=op11,
        op12_question_need_observation_rows_normalization=op12,
    )

    assert material["rating_question_consistency_status_ref"] == elr.P7_R54_AHR_POST_ALR12_ELR_OP13_STATUS_PASSED_REF
    assert material["emlis_readfeel_repair_required_case_refs"] == ["elr_op04_case_ref_001_bodyfree"]
    assert material["p5_surface_repair_required_case_refs"] == ["elr_op04_case_ref_002_bodyfree"]
    assert material["gate_boundary_required_case_refs"] == ["elr_op04_case_ref_003_bodyfree"]
    assert material["execution_blocker_case_refs"] == ["elr_op04_case_ref_004_bodyfree"]
    assert material["question_candidate_case_refs"] == []
    assert material["p8_start_allowed_here"] is False
    assert material["next_required_step"] == elr.P7_R54_AHR_POST_ALR12_ELR_OP14_STEP_REF
    assert elr.assert_p7_r54_ahr_post_alr12_elr_op13_rating_question_consistency_blocker_separation_contract(material) is True


def test_elr_op13_repairs_when_op12_contract_is_invalid() -> None:
    op11 = _op11_normalized()
    op12 = _op12_normalized()
    op12["question_need_observation_row_count"] = 23
    material = elr.build_p7_r54_ahr_post_alr12_elr_op13_rating_question_consistency_blocker_separation(
        op11_rating_rows_normalization=op11,
        op12_question_need_observation_rows_normalization=op12,
    )

    assert material["rating_question_consistency_status_ref"] == elr.P7_R54_AHR_POST_ALR12_ELR_OP13_STATUS_REPAIR_REQUIRED_REF
    assert material["rating_question_consistency_repair_required"] is True
    assert any(
        ref in {
            "elr_op13_op12_question_need_rows_contract_invalid",
            "elr_op13_op12_question_need_rows_contract_invalid_or_missing",
        }
        for ref in material["elr_op13_blocker_refs"]
    )
    assert material["ready_for_disposal_purge_receipt_intake"] is False
    assert material["next_required_step"] == elr.P7_R54_AHR_POST_ALR12_ELR_NEXT_STEP_REPAIR_RATING_QUESTION_CONSISTENCY_REF
    assert elr.assert_p7_r54_ahr_post_alr12_elr_op13_rating_question_consistency_blocker_separation_contract(material) is True


@pytest.mark.parametrize(
    ("field", "bad_value"),
    [
        ("rating_question_consistency_passed", False),
        ("ready_for_disposal_purge_receipt_intake", False),
        ("p8_start_allowed_here", True),
        ("p8_question_implementation_allowed", True),
        ("actual_review_evidence_complete_here", True),
        ("next_required_step", "P8_START"),
    ],
)
def test_elr_op13_contract_rejects_passed_mutations(field: str, bad_value: object) -> None:
    op11 = _op11_normalized()
    op12 = _op12_normalized()
    material = elr.build_p7_r54_ahr_post_alr12_elr_op13_rating_question_consistency_blocker_separation(
        op11_rating_rows_normalization=op11,
        op12_question_need_observation_rows_normalization=op12,
    )
    material[field] = bad_value

    with pytest.raises(ValueError):
        elr.assert_p7_r54_ahr_post_alr12_elr_op13_rating_question_consistency_blocker_separation_contract(material)


def test_elr_op12_op13_full_operation_aliases_match_canonical_functions() -> None:
    op11 = _op11_normalized()
    op12 = elr.build_p7_r54_ahr_post_alr12_explicit_local_only_review_start_retry_operation_elr_op12_question_need_observation_rows_normalization(
        op11_rating_rows_normalization=op11,
        question_need_observation_rows=_valid_question_need_rows(_op10_accepted(), op11),
    )
    assert elr.assert_p7_r54_ahr_post_alr12_explicit_local_only_review_start_retry_operation_elr_op12_question_need_observation_rows_normalization_contract(op12) is True
    op13 = elr.build_p7_r54_ahr_post_alr12_explicit_local_only_review_start_retry_operation_elr_op13_rating_question_consistency_blocker_separation(
        op11_rating_rows_normalization=op11,
        op12_question_need_observation_rows_normalization=op12,
    )
    assert elr.assert_p7_r54_ahr_post_alr12_explicit_local_only_review_start_retry_operation_elr_op13_rating_question_consistency_blocker_separation_contract(op13) is True
    assert op13["rating_question_consistency_status_ref"] == elr.P7_R54_AHR_POST_ALR12_ELR_OP13_STATUS_PASSED_REF


def test_elr_op12_op13_result_memo_is_bodyfree_and_current_scope_only() -> None:
    memo_path = TEST_DIR / "R54_AHR_PostALR12_ExplicitLocalOnlyReviewStartRetryOperation_ELR_OP00_OP13_Result_20260704.md"
    text = memo_path.read_text(encoding="utf-8")

    assert "ELR-OP12" in text
    assert "ELR-OP13" in text
    assert "actual local-only human review execution: not performed" in text
    assert "p8_question_spec_created: false" in text
    assert "release_allowed: false" in text
    assert "ELR-OP14: disposal / purge receipt intake" in text
    assert "raw_input:" not in text
    assert "comment_text:" not in text
    assert "question_text:" not in text
    assert "local_path:" not in text
    assert "body_hash:" not in text
    assert "terminal_output:" not in text
