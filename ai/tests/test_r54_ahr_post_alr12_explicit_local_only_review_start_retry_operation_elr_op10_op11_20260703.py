# -*- coding: utf-8 -*-
"""R54-AHR Post-ALR12 explicit local-only review start/retry ELR-OP10/OP11 tests."""

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
from test_r54_ahr_post_alr12_explicit_local_only_review_start_retry_operation_elr_op08_op09_20260703 import (  # noqa: E501
    _op08_completed,
    _valid_actual_operation_receipt,
)

_OP09_ACCEPTED_CACHE: dict[str, object] | None = None
_OP10_ACCEPTED_CACHE: dict[str, object] | None = None


def _op09_accepted() -> dict[str, object]:
    global _OP09_ACCEPTED_CACHE
    if _OP09_ACCEPTED_CACHE is None:
        material = elr.build_p7_r54_ahr_post_alr12_elr_op09_actual_operation_receipt_intake(
            actual_review_operation_lifecycle_state_capture=_op08_completed(),
            actual_operation_receipt_optional=_valid_actual_operation_receipt(),
        )
        assert material["actual_operation_receipt_status_ref"] == elr.P7_R54_AHR_POST_ALR12_ELR_OP09_STATUS_ACCEPTED_BODYFREE_REF
        assert elr.assert_p7_r54_ahr_post_alr12_elr_op09_actual_operation_receipt_intake_contract(material) is True
        _OP09_ACCEPTED_CACHE = material
    return deepcopy(_OP09_ACCEPTED_CACHE)


def _case_refs() -> list[str]:
    return [f"elr_op04_case_ref_{index:03d}_bodyfree" for index in range(1, 25)]


def _valid_sanitized_rows(
    *,
    score_overrides_by_index: dict[int, dict[str, float]] | None = None,
    readfeel_blockers_by_index: dict[int, list[str]] | None = None,
) -> list[dict[str, object]]:
    op09 = _op09_accepted()
    rows: list[dict[str, object]] = []
    score_overrides_by_index = score_overrides_by_index or {}
    readfeel_blockers_by_index = readfeel_blockers_by_index or {}
    for index, case_ref in enumerate(_case_refs(), start=1):
        axis_score_refs = {axis_ref: 1.0 for axis_ref in elr.P7_R54_AHR_POST_ALR12_ELR_RATING_AXIS_REFS}
        axis_score_refs.update(score_overrides_by_index.get(index, {}))
        axis_pass_flags = {
            axis_ref: axis_score_refs[axis_ref] >= elr.P7_R54_AHR_POST_ALR12_ELR_RATING_AXIS_TARGET_THRESHOLDS[axis_ref]
            for axis_ref in elr.P7_R54_AHR_POST_ALR12_ELR_RATING_AXIS_REFS
        }
        below_target = [axis_ref for axis_ref, passed in axis_pass_flags.items() if not passed]
        rows.append(
            {
                "schema_version": elr.P7_R54_AHR_POST_ALR12_ELR_SANITIZED_REVIEW_RESULT_ROW_SCHEMA_VERSION,
                "review_session_id": str(op09["review_session_id"]),
                "operation_receipt_ref": str(op09["operation_receipt_ref"]),
                "review_result_row_ref": f"elr_op10_sanitized_review_result_row_{index:03d}_bodyfree",
                "case_ref": case_ref,
                "reviewer_person_ref": str(op09["reviewer_person_ref"]),
                "source_kind_ref": elr.P7_R54_AHR_POST_ALR12_ELR_ACTUAL_REVIEW_SOURCE_KIND_REF,
                "verdict_ref": "YELLOW" if below_target else "PASS",
                "axis_score_refs": axis_score_refs,
                "axis_score_count": len(elr.P7_R54_AHR_POST_ALR12_ELR_RATING_AXIS_REFS),
                "axis_pass_flags": axis_pass_flags,
                "sanitized_reason_id_refs": ["selection_only_actual_review_result_bodyfree"],
                "readfeel_blocker_id_refs": readfeel_blockers_by_index.get(index, []),
                "execution_blocker_id_refs": [],
                "question_need_primary_class_ref": "no_question_needed_emlis_can_observe",
                "ambiguity_kind_refs": ["no_material_ambiguity"],
                "one_question_fit_ref": "not_needed",
                "repair_required_refs": [],
                "selection_only": True,
                "raw_input_included": False,
                "comment_text_body_included": False,
                "returned_surface_body_included": False,
                "reviewer_free_text_included": False,
                "reviewer_note_body_included": False,
                "question_text_included": False,
                "draft_question_text_included": False,
                "answer_text_included": False,
                "local_path_included": False,
                "body_hash_included": False,
                "terminal_output_body_included": False,
                "row_created_by_helper": False,
                "row_created_for_unit_test": False,
                "row_is_synthetic_contract_fixture": False,
                "historical_row_reused": False,
                "body_free": True,
            }
        )
    return rows


def _op10_accepted() -> dict[str, object]:
    global _OP10_ACCEPTED_CACHE
    if _OP10_ACCEPTED_CACHE is None:
        rows = _valid_sanitized_rows()
        material = elr.build_p7_r54_ahr_post_alr12_elr_op10_sanitized_review_result_rows_intake_provenance_guard(
            actual_operation_receipt_intake=_op09_accepted(),
            sanitized_review_result_rows_optional=rows,
            expected_case_refs=_case_refs(),
        )
        assert material["sanitized_rows_status_ref"] == elr.P7_R54_AHR_POST_ALR12_ELR_OP10_STATUS_ACCEPTED_BODYFREE_REF
        assert elr.assert_p7_r54_ahr_post_alr12_elr_op10_sanitized_review_result_rows_intake_provenance_guard_contract(material) is True
        _OP10_ACCEPTED_CACHE = material
    return deepcopy(_OP10_ACCEPTED_CACHE)


def test_elr_op10_missing_sanitized_rows_waits_without_rating_or_complete_claim() -> None:
    material = elr.build_p7_r54_ahr_post_alr12_elr_op10_sanitized_review_result_rows_intake_provenance_guard(
        actual_operation_receipt_intake=_op09_accepted(),
        expected_case_refs=_case_refs(),
    )

    assert set(material) == set(elr.P7_R54_AHR_POST_ALR12_ELR_OP10_REQUIRED_FIELD_REFS)
    assert material["schema_version"] == elr.P7_R54_AHR_POST_ALR12_ELR_OP10_SCHEMA_VERSION
    assert material["op09_actual_operation_receipt_accepted"] is True
    assert material["sanitized_review_result_rows_present"] is False
    assert material["sanitized_rows_status_ref"] == elr.P7_R54_AHR_POST_ALR12_ELR_OP10_STATUS_MISSING_WAITING_REF
    assert material["sanitized_review_result_rows_missing_waiting"] is True
    assert material["ready_for_rating_rows_normalization"] is False
    assert material["actual_sanitized_review_result_rows_from_real_operation_accepted"] is False
    assert material["actual_review_evidence_complete_here"] is False
    assert material["next_required_step"] == elr.P7_R54_AHR_POST_ALR12_ELR_NEXT_STEP_PROVIDE_SANITIZED_REVIEW_RESULT_ROWS_REF
    assert elr.assert_p7_r54_ahr_post_alr12_elr_op10_sanitized_review_result_rows_intake_provenance_guard_contract(material) is True
    _assert_common_bodyfree_no_touch_no_promotion(material)


def test_elr_op10_accepts_24_bodyfree_actual_review_sanitized_rows_without_rating_or_promotion() -> None:
    material = _op10_accepted()

    assert set(material) == set(elr.P7_R54_AHR_POST_ALR12_ELR_OP10_REQUIRED_FIELD_REFS)
    assert material["sanitized_rows_status_ref"] == elr.P7_R54_AHR_POST_ALR12_ELR_OP10_STATUS_ACCEPTED_BODYFREE_REF
    assert material["sanitized_review_result_rows_accepted"] is True
    assert material["sanitized_review_result_row_count"] == 24
    assert material["sanitized_review_result_row_count_is_24"] is True
    assert material["case_refs_unique"] is True
    assert material["case_refs_match_expected_manifest"] is True
    assert material["rows_bodyfree_only"] is True
    assert material["rows_selection_only"] is True
    assert material["rows_have_actual_person_selection_only_provenance"] is True
    assert material["row_provenance_guard_passed"] is True
    assert material["rating_rows_normalization_required_next"] is True
    assert material["actual_sanitized_review_result_rows_created_here_by_helper"] is False
    assert material["actual_rows_created_here_by_helper"] is False
    assert material["actual_review_evidence_complete_here"] is False
    assert material["elr_op10_blocker_refs"] == []
    assert material["next_required_step"] == elr.P7_R54_AHR_POST_ALR12_ELR_OP11_STEP_REF
    assert elr.assert_p7_r54_ahr_post_alr12_elr_op10_sanitized_review_result_rows_intake_provenance_guard_contract(material) is True
    _assert_common_bodyfree_no_touch_no_promotion(material)


@pytest.mark.parametrize(
    ("field", "bad_value", "expected_blocker"),
    [
        ("source_kind_ref", "synthetic_rows", "elr_op10_sanitized_row_source_kind_not_actual_local_only_human_review_by_person"),
        ("row_created_by_helper", True, "elr_op10_row_created_by_helper_mismatch"),
        ("row_created_for_unit_test", True, "elr_op10_row_created_for_unit_test_mismatch"),
        ("row_is_synthetic_contract_fixture", True, "elr_op10_row_is_synthetic_contract_fixture_mismatch"),
        ("historical_row_reused", True, "elr_op10_historical_row_reused_mismatch"),
        ("question_text_included", True, "elr_op10_question_text_included_mismatch"),
        ("axis_score_count", 5, "elr_op10_axis_score_count_mismatch"),
        ("question_need_primary_class_ref", "p8_question_spec", "elr_op10_question_need_primary_class_ref_not_allowed"),
    ],
)
def test_elr_op10_rejects_invalid_source_or_payload_marker_or_axis_material(
    field: str, bad_value: object, expected_blocker: str
) -> None:
    rows = _valid_sanitized_rows()
    rows[0][field] = bad_value
    material = elr.build_p7_r54_ahr_post_alr12_elr_op10_sanitized_review_result_rows_intake_provenance_guard(
        actual_operation_receipt_intake=_op09_accepted(),
        sanitized_review_result_rows_optional=rows,
        expected_case_refs=_case_refs(),
    )

    assert material["sanitized_rows_status_ref"] == elr.P7_R54_AHR_POST_ALR12_ELR_OP10_STATUS_INVALID_OR_REPAIR_REQUIRED_REF
    assert expected_blocker in material["elr_op10_blocker_refs"]
    assert material["sanitized_review_result_rows_accepted"] is False
    assert material["ready_for_rating_rows_normalization"] is False
    assert material["next_required_step"] == elr.P7_R54_AHR_POST_ALR12_ELR_NEXT_STEP_REPAIR_SANITIZED_REVIEW_RESULT_ROWS_REF
    assert elr.assert_p7_r54_ahr_post_alr12_elr_op10_sanitized_review_result_rows_intake_provenance_guard_contract(material) is True


def test_elr_op10_rejects_forbidden_payload_key_without_leaking_body_value() -> None:
    rows = _valid_sanitized_rows()
    rows[0]["raw_input"] = "body-full sanitized row must never leak"
    material = elr.build_p7_r54_ahr_post_alr12_elr_op10_sanitized_review_result_rows_intake_provenance_guard(
        actual_operation_receipt_intake=_op09_accepted(),
        sanitized_review_result_rows_optional=rows,
        expected_case_refs=_case_refs(),
    )

    assert material["sanitized_rows_status_ref"] == elr.P7_R54_AHR_POST_ALR12_ELR_OP10_STATUS_INVALID_OR_REPAIR_REQUIRED_REF
    assert material["sanitized_rows_forbidden_payload_key_paths"] == ["sanitized_review_result_rows[0].raw_input"]
    assert "body-full sanitized row must never leak" not in repr(material)
    assert "elr_op10_sanitized_rows_forbidden_payload_key_detected" in material["elr_op10_blocker_refs"]
    assert elr.assert_p7_r54_ahr_post_alr12_elr_op10_sanitized_review_result_rows_intake_provenance_guard_contract(material) is True


def test_elr_op10_rejects_incomplete_or_manifest_mismatched_rows() -> None:
    incomplete_rows = _valid_sanitized_rows()[:-1]
    incomplete = elr.build_p7_r54_ahr_post_alr12_elr_op10_sanitized_review_result_rows_intake_provenance_guard(
        actual_operation_receipt_intake=_op09_accepted(),
        sanitized_review_result_rows_optional=incomplete_rows,
        expected_case_refs=_case_refs(),
    )
    assert incomplete["sanitized_rows_status_ref"] == elr.P7_R54_AHR_POST_ALR12_ELR_OP10_STATUS_INVALID_OR_REPAIR_REQUIRED_REF
    assert "elr_op10_sanitized_review_result_row_count_not_24" in incomplete["elr_op10_blocker_refs"]
    assert elr.assert_p7_r54_ahr_post_alr12_elr_op10_sanitized_review_result_rows_intake_provenance_guard_contract(incomplete) is True

    mismatched_rows = _valid_sanitized_rows()
    mismatched_rows[0]["case_ref"] = "elr_op04_case_ref_unexpected_001_bodyfree"
    mismatched = elr.build_p7_r54_ahr_post_alr12_elr_op10_sanitized_review_result_rows_intake_provenance_guard(
        actual_operation_receipt_intake=_op09_accepted(),
        sanitized_review_result_rows_optional=mismatched_rows,
        expected_case_refs=_case_refs(),
    )
    assert mismatched["sanitized_rows_status_ref"] == elr.P7_R54_AHR_POST_ALR12_ELR_OP10_STATUS_INVALID_OR_REPAIR_REQUIRED_REF
    assert "elr_op10_case_refs_do_not_match_expected_manifest" in mismatched["elr_op10_blocker_refs"]
    assert elr.assert_p7_r54_ahr_post_alr12_elr_op10_sanitized_review_result_rows_intake_provenance_guard_contract(mismatched) is True


def test_elr_op10_invalid_op09_goes_to_repair() -> None:
    op09 = _op09_accepted()
    op09["release_allowed"] = True
    material = elr.build_p7_r54_ahr_post_alr12_elr_op10_sanitized_review_result_rows_intake_provenance_guard(
        actual_operation_receipt_intake=op09,
        sanitized_review_result_rows_optional=_valid_sanitized_rows(),
        expected_case_refs=_case_refs(),
    )

    assert material["sanitized_rows_status_ref"] == elr.P7_R54_AHR_POST_ALR12_ELR_OP10_STATUS_INVALID_OR_REPAIR_REQUIRED_REF
    assert "elr_op10_op09_actual_operation_receipt_intake_contract_invalid_or_missing" in material["elr_op10_blocker_refs"]
    assert material["next_required_step"] == elr.P7_R54_AHR_POST_ALR12_ELR_NEXT_STEP_REPAIR_SANITIZED_REVIEW_RESULT_ROWS_REF
    assert elr.assert_p7_r54_ahr_post_alr12_elr_op10_sanitized_review_result_rows_intake_provenance_guard_contract(material) is True


@pytest.mark.parametrize(
    ("field", "bad_value"),
    [
        ("sanitized_review_result_rows_accepted", False),
        ("sanitized_review_result_row_count", 23),
        ("actual_sanitized_review_result_rows_created_here_by_helper", True),
        ("rating_rows_normalization_required_next", False),
        ("actual_review_evidence_complete_here", True),
        ("p8_start_allowed", True),
    ],
)
def test_elr_op10_contract_rejects_accepted_rows_mutations(field: str, bad_value: object) -> None:
    material = _op10_accepted()
    material[field] = bad_value

    with pytest.raises(ValueError):
        elr.assert_p7_r54_ahr_post_alr12_elr_op10_sanitized_review_result_rows_intake_provenance_guard_contract(material)


def test_elr_op11_waits_when_op10_rows_are_still_missing() -> None:
    op10_missing = elr.build_p7_r54_ahr_post_alr12_elr_op10_sanitized_review_result_rows_intake_provenance_guard(
        actual_operation_receipt_intake=_op09_accepted(),
        expected_case_refs=_case_refs(),
    )
    material = elr.build_p7_r54_ahr_post_alr12_elr_op11_rating_rows_normalization_threshold_summary(
        sanitized_review_result_rows_intake=op10_missing,
    )

    assert set(material) == set(elr.P7_R54_AHR_POST_ALR12_ELR_OP11_REQUIRED_FIELD_REFS)
    assert material["rating_rows_status_ref"] == elr.P7_R54_AHR_POST_ALR12_ELR_OP11_STATUS_MISSING_WAITING_REF
    assert material["rating_rows_missing_waiting"] is True
    assert material["rating_rows_normalized"] is False
    assert material["question_need_observation_row_normalization_allowed_next"] is False
    assert material["actual_review_evidence_complete_here"] is False
    assert material["next_required_step"] == elr.P7_R54_AHR_POST_ALR12_ELR_NEXT_STEP_PROVIDE_SANITIZED_REVIEW_RESULT_ROWS_REF
    assert elr.assert_p7_r54_ahr_post_alr12_elr_op11_rating_rows_normalization_threshold_summary_contract(material) is True
    _assert_common_bodyfree_no_touch_no_promotion(material)


def test_elr_op11_normalizes_rating_rows_from_accepted_sanitized_rows_without_completing_actual_evidence() -> None:
    material = elr.build_p7_r54_ahr_post_alr12_elr_op11_rating_rows_normalization_threshold_summary(
        sanitized_review_result_rows_intake=_op10_accepted(),
    )

    assert set(material) == set(elr.P7_R54_AHR_POST_ALR12_ELR_OP11_REQUIRED_FIELD_REFS)
    assert material["schema_version"] == elr.P7_R54_AHR_POST_ALR12_ELR_OP11_SCHEMA_VERSION
    assert material["rating_rows_status_ref"] == elr.P7_R54_AHR_POST_ALR12_ELR_OP11_STATUS_NORMALIZED_BODYFREE_REF
    assert material["rating_rows_normalized"] is True
    assert material["rating_row_count"] == 24
    assert material["rating_row_count_is_24"] is True
    assert material["axis_target_thresholds_present"] is True
    assert material["actual_rating_rows_normalized_from_actual_rows"] is True
    assert material["rating_decision_material_only"] is True
    assert material["question_need_observation_row_normalization_allowed_next"] is True
    assert material["actual_review_evidence_complete_here"] is False
    assert material["elr_op11_blocker_refs"] == []
    assert material["next_required_step"] == elr.P7_R54_AHR_POST_ALR12_ELR_OP12_STEP_REF
    for row in material["rating_rows"]:
        assert set(row) == set(elr.P7_R54_AHR_POST_ALR12_ELR_OP11_REQUIRED_RATING_ROW_FIELD_REFS)
        assert row["actual_rating_row_from_real_operation"] is True
        assert row["rating_decision_material_only"] is True
        assert row["body_free"] is True
    assert elr.assert_p7_r54_ahr_post_alr12_elr_op11_rating_rows_normalization_threshold_summary_contract(material) is True
    _assert_common_bodyfree_no_touch_no_promotion(material)


def test_elr_op11_threshold_summary_preserves_below_target_axis_bodyfree() -> None:
    rows = _valid_sanitized_rows(
        score_overrides_by_index={1: {"creepy_absence": 0.25}},
        readfeel_blockers_by_index={1: ["creepy_absence_low_bodyfree"]},
    )
    op10 = elr.build_p7_r54_ahr_post_alr12_elr_op10_sanitized_review_result_rows_intake_provenance_guard(
        actual_operation_receipt_intake=_op09_accepted(),
        sanitized_review_result_rows_optional=rows,
        expected_case_refs=_case_refs(),
    )
    assert elr.assert_p7_r54_ahr_post_alr12_elr_op10_sanitized_review_result_rows_intake_provenance_guard_contract(op10) is True

    material = elr.build_p7_r54_ahr_post_alr12_elr_op11_rating_rows_normalization_threshold_summary(
        sanitized_review_result_rows_intake=op10,
    )

    assert material["rating_rows_status_ref"] == elr.P7_R54_AHR_POST_ALR12_ELR_OP11_STATUS_NORMALIZED_BODYFREE_REF
    assert "creepy_absence" in material["below_target_axis_refs"]
    assert material["all_axis_target_passed"] is False
    assert material["average_axis_scores"]["creepy_absence"] < 1.0
    assert material["readfeel_blocker_count_ref"] == 1
    assert elr.assert_p7_r54_ahr_post_alr12_elr_op11_rating_rows_normalization_threshold_summary_contract(material) is True


def test_elr_op11_invalid_op10_goes_to_repair() -> None:
    op10 = _op10_accepted()
    op10["p8_start_allowed"] = True
    material = elr.build_p7_r54_ahr_post_alr12_elr_op11_rating_rows_normalization_threshold_summary(
        sanitized_review_result_rows_intake=op10,
    )

    assert material["rating_rows_status_ref"] == elr.P7_R54_AHR_POST_ALR12_ELR_OP11_STATUS_INVALID_OR_REPAIR_REQUIRED_REF
    assert "elr_op11_op10_sanitized_rows_contract_invalid_or_missing" in material["elr_op11_blocker_refs"]
    assert material["rating_rows_normalized"] is False
    assert material["next_required_step"] == elr.P7_R54_AHR_POST_ALR12_ELR_NEXT_STEP_REPAIR_RATING_ROWS_NORMALIZATION_REF
    assert elr.assert_p7_r54_ahr_post_alr12_elr_op11_rating_rows_normalization_threshold_summary_contract(material) is True


@pytest.mark.parametrize(
    ("field", "bad_value"),
    [
        ("rating_rows_normalized", False),
        ("rating_row_count", 23),
        ("rating_decision_material_only", False),
        ("question_need_observation_row_normalization_allowed_next", False),
        ("actual_review_evidence_complete_here", True),
        ("p8_start_allowed", True),
    ],
)
def test_elr_op11_contract_rejects_normalized_rating_mutations(field: str, bad_value: object) -> None:
    material = elr.build_p7_r54_ahr_post_alr12_elr_op11_rating_rows_normalization_threshold_summary(
        sanitized_review_result_rows_intake=_op10_accepted(),
    )
    material[field] = bad_value

    with pytest.raises(ValueError):
        elr.assert_p7_r54_ahr_post_alr12_elr_op11_rating_rows_normalization_threshold_summary_contract(material)


def test_elr_op11_contract_rejects_rating_row_bodyfree_mutation() -> None:
    material = elr.build_p7_r54_ahr_post_alr12_elr_op11_rating_rows_normalization_threshold_summary(
        sanitized_review_result_rows_intake=_op10_accepted(),
    )
    rating_rows = deepcopy(material["rating_rows"])
    rating_rows[0]["body_free"] = False
    material["rating_rows"] = rating_rows

    with pytest.raises(ValueError):
        elr.assert_p7_r54_ahr_post_alr12_elr_op11_rating_rows_normalization_threshold_summary_contract(material)


def test_elr_op10_op11_alias_builders_and_contracts_match_canonical_functions() -> None:
    op10 = elr.build_p7_r54_ahr_post_alr12_explicit_local_only_review_start_retry_operation_elr_op10_sanitized_review_result_rows_intake_provenance_guard(
        actual_operation_receipt_intake=_op09_accepted(),
        sanitized_review_result_rows_optional=_valid_sanitized_rows(),
        expected_case_refs=_case_refs(),
    )
    assert elr.assert_p7_r54_ahr_post_alr12_explicit_local_only_review_start_retry_operation_elr_op10_sanitized_review_result_rows_intake_provenance_guard_contract(op10) is True

    op11 = elr.build_p7_r54_ahr_post_alr12_explicit_local_only_review_start_retry_operation_elr_op11_rating_rows_normalization_threshold_summary(
        sanitized_review_result_rows_intake=op10,
    )
    assert elr.assert_p7_r54_ahr_post_alr12_explicit_local_only_review_start_retry_operation_elr_op11_rating_rows_normalization_threshold_summary_contract(op11) is True


def test_elr_op10_op11_result_memo_is_bodyfree_and_limited_to_current_scope() -> None:
    result_memo = TEST_DIR / "R54_AHR_PostALR12_ExplicitLocalOnlyReviewStartRetryOperation_ELR_OP00_OP11_Result_20260703.md"
    text = result_memo.read_text(encoding="utf-8")

    for heading in (
        "## 1. Implementation scope",
        "## 2. Changed files",
        "## 3. Prior implementation confirmation",
        "## 4. ELR-OP10",
        "## 5. ELR-OP11",
        "## 6. Test results",
        "## 7. Not claimed",
        "## 8. Next required step",
    ):
        assert heading in text
    assert "ELR-OP12" in text
    assert "actual_local_human_review_execution_by_helper: false" in text
    assert "sanitized_review_result_rows_created_here_by_helper: false" in text
    assert "actual_review_evidence_complete: false" in text
    forbidden_literals = (
        "raw_input:",
        "comment_text:",
        "question_text:",
        "draft_question_text:",
        "terminal output body",
        "body-full sanitized row must never leak",
    )
    for literal in forbidden_literals:
        assert literal not in text
