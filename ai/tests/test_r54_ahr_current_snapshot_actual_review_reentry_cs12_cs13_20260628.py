# -*- coding: utf-8 -*-
"""R54-AHR-CS12/CS13 current snapshot actual review re-entry contract tests."""

from __future__ import annotations

from copy import deepcopy
from typing import Any

import pytest

import emlis_ai_p7_r54_ahr_current_snapshot_actual_review_reentry_20260628 as cs
from test_r54_ahr_current_snapshot_actual_review_reentry_cs10_cs11_20260628 import _build_ready_cs11


FORBIDDEN_BODY_OR_QUESTION_KEYS = (
    "raw_input",
    "raw_body",
    "returned_emlis_body",
    "history_surface",
    "comment_text",
    "comment_text_body",
    "reviewer_free_text",
    "reviewer_note",
    "reviewer_notes",
    "reviewer_notes_body",
    "question_text",
    "draft_question_text",
    "raw_question_answer",
    "body_full_packet_content",
    "packet_content",
    "local_absolute_path",
    "local_file_path",
    "body_hash",
    "terminal_output_body",
    "stdout_body",
    "stderr_body",
    "traceback_body",
)


def _assert_bodyfree_no_touch_allowing(material: dict[str, Any], allowed_true_flags: tuple[str, ...]) -> None:
    assert material["body_free"] is True
    for key in cs.P7_R54_AHR_CS_FALSE_FLAG_REFS:
        if key in allowed_true_flags:
            continue
        assert material[key] is False, key
    for flag_map_key in ("public_contract", "r54_ahr_cs_no_touch_contract", "body_free_markers"):
        assert material[flag_map_key]
        assert all(value is False for value in material[flag_map_key].values()), flag_map_key
    for forbidden_key in FORBIDDEN_BODY_OR_QUESTION_KEYS:
        assert forbidden_key not in material


def _build_ready_cs12(*, mixed: bool = False) -> dict[str, Any]:
    material = cs.build_p7_r54_ahr_cs12_blocker_question_need_observation_normalization(
        rating_row_normalization=_build_ready_cs11(mixed=mixed)
    )
    assert cs.assert_p7_r54_ahr_cs12_blocker_question_need_observation_normalization_contract(material) is True
    return material


def _build_ready_cs13(*, mixed: bool = False) -> dict[str, Any]:
    material = cs.build_p7_r54_ahr_cs13_rating_question_consistency_guard(
        blocker_question_need_observation_normalization=_build_ready_cs12(mixed=mixed)
    )
    assert cs.assert_p7_r54_ahr_cs13_rating_question_consistency_guard_contract(material) is True
    return material


def test_cs00_to_cs11_ready_path_is_present_before_cs12_cs13() -> None:
    cs11 = _build_ready_cs11()

    assert cs11["rating_row_normalization_status_ref"] == cs.P7_R54_AHR_CS11_NORMALIZED_STATUS_REF
    assert cs11["rating_row_count"] == 24
    assert cs11["actual_rating_rows_materialized_here"] is True
    assert cs11["blocker_question_need_observation_normalization_allowed_next"] is True
    assert cs11["next_required_step"] == cs.P7_R54_AHR_CS12_STEP_REF
    assert cs.assert_p7_r54_ahr_cs11_rating_row_normalization_contract(cs11) is True


def test_cs12_default_is_fail_closed_without_ready_cs11() -> None:
    material = cs.build_p7_r54_ahr_cs12_blocker_question_need_observation_normalization()

    assert material["blocker_question_need_observation_normalization_status_ref"] == cs.P7_R54_AHR_CS12_BLOCKED_STATUS_REF
    assert material["question_need_observation_row_count"] == 0
    assert material["question_need_observation_rows"] == []
    assert material["blocker_row_count"] == 0
    assert material["blocker_rows"] == []
    assert material["actual_question_need_observation_rows_materialized_here"] is False
    assert material["rating_question_consistency_guard_allowed_next"] is False
    assert material["next_required_step"] == cs.P7_R54_AHR_CS12_BLOCKED_NEXT_REQUIRED_STEP_REF
    _assert_bodyfree_no_touch_allowing(material, ())
    assert cs.assert_p7_r54_ahr_cs12_blocker_question_need_observation_normalization_contract(material) is True


def test_cs12_ready_normalizes_question_observation_rows_bodyfree() -> None:
    material = _build_ready_cs12()

    assert set(material) == set(cs.P7_R54_AHR_CS12_BLOCKER_QUESTION_NEED_OBSERVATION_NORMALIZATION_REQUIRED_FIELD_REFS)
    assert material["schema_version"] == cs.P7_R54_AHR_CS12_BLOCKER_QUESTION_NEED_OBSERVATION_NORMALIZATION_SCHEMA_VERSION
    assert material["policy_section"] == cs.P7_R54_AHR_CS12_STEP_REF
    assert material["operation_step_ref"] == cs.P7_R54_AHR_CS12_STEP_REF
    assert material["cs11_next_required_step"] == cs.P7_R54_AHR_CS12_STEP_REF
    assert material["current_basis_ref"] == cs.P7_R54_AHR_CS_ACTUAL_REVIEW_BASIS_REF
    assert material["historical_basis_ref"] == cs.P7_R54_AHR_CS_EXISTING_AHR_BASIS_REF
    assert material["blocker_question_need_observation_normalization_status_ref"] == cs.P7_R54_AHR_CS12_NORMALIZED_STATUS_REF
    assert material["blocker_question_need_observation_normalization_reason_refs"] == [cs.P7_R54_AHR_CS12_READY_REASON_REF]
    assert material["source_rating_row_count"] == 24
    assert material["source_rating_row_ref_count"] == 24
    assert material["question_need_observation_row_count"] == 24
    assert material["actual_question_need_observation_row_count"] == 24
    assert material["question_need_observation_row_ref_count"] == 24
    assert material["case_ref_ids_unique"] is True
    assert material["question_need_primary_class_counts"] == {"no_question_needed_emlis_can_observe": 24}
    assert material["blocker_row_count"] == 0
    assert material["readfeel_blocker_row_count"] == 0
    assert material["execution_blocker_row_count"] == 0
    assert material["question_observation_rows_bodyfree_only"] is True
    assert material["question_observation_rows_from_actual_review_only"] is True
    assert material["question_observation_rows_have_allowed_primary_class_refs"] is True
    assert material["question_observation_rows_have_allowed_ambiguity_kind_refs"] is True
    assert material["question_observation_rows_have_allowed_one_question_fit_refs"] is True
    assert material["question_observation_rows_have_allowed_repair_required_refs"] is True
    assert material["question_text_included"] is False
    assert material["draft_question_text_included"] is False
    assert material["p8_implementation_spec_finalized_here"] is False
    assert material["question_need_observation_rows_materialized_here"] is True
    assert material["actual_question_need_observation_rows_materialized_here"] is True
    assert material["rating_question_consistency_guard_allowed_next"] is True
    assert material["p8_material_candidate_row_count"] == 0
    assert material["actual_review_evidence_complete"] is False
    assert material["p8_start_allowed"] is False
    assert material["release_allowed"] is False
    assert tuple(material["implemented_steps"]) == cs.P7_R54_AHR_CS12_IMPLEMENTED_STEPS
    assert tuple(material["not_yet_implemented_steps"]) == cs.P7_R54_AHR_CS12_NOT_YET_IMPLEMENTED_STEPS
    assert material["next_required_step"] == cs.P7_R54_AHR_CS13_STEP_REF
    _assert_bodyfree_no_touch_allowing(material, cs.P7_R54_AHR_CS12_ALLOWED_TRUE_FALSE_FLAG_REFS)


def test_cs12_rows_preserve_source_refs_and_bodyfree_boundaries() -> None:
    material = _build_ready_cs12(mixed=True)

    for row in material["blocker_rows"]:
        assert set(row) == set(cs.P7_R54_AHR_CS12_BLOCKER_ROW_REQUIRED_FIELD_REFS)
        assert row["schema_version"] == cs.P7_R54_AHR_CS12_BLOCKER_ROW_SCHEMA_VERSION
        assert row["source_rating_row_ref"].startswith("rating_row_")
        assert row["source_review_result_row_ref"].startswith("review_result_row_")
        assert row["current_basis_ref"] == cs.P7_R54_AHR_CS_ACTUAL_REVIEW_BASIS_REF
        assert row["blocker_status"] == cs.P7_R54_AHR_CS12_BLOCKER_STATUS_OPEN_REF
        assert row["body_free"] is True
        for flag_ref in cs.P7_R54_AHR_CS12_ROW_BODYFREE_FALSE_FLAG_REFS:
            assert row[flag_ref] is False

    for row in material["question_need_observation_rows"]:
        assert set(row) == set(cs.P7_R54_AHR_CS12_QUESTION_NEED_OBSERVATION_ROW_REQUIRED_FIELD_REFS)
        assert row["schema_version"] == cs.P7_R54_AHR_CS12_QUESTION_NEED_OBSERVATION_ROW_SCHEMA_VERSION
        assert row["review_session_id"] == cs.P7_R54_AHR_CS_DEFAULT_REVIEW_SESSION_ID
        assert row["source_rating_row_ref"].startswith("rating_row_")
        assert row["source_review_result_row_ref"].startswith("review_result_row_")
        assert row["question_observation_row_ref"].startswith("question_observation_row_")
        assert row["current_basis_ref"] == cs.P7_R54_AHR_CS_ACTUAL_REVIEW_BASIS_REF
        assert row["p8_implementation_spec_finalized_here"] is False
        assert row["body_free"] is True
        for flag_ref in cs.P7_R54_AHR_CS12_ROW_BODYFREE_FALSE_FLAG_REFS:
            assert row[flag_ref] is False


def test_cs12_mixed_rows_count_blockers_repairs_and_keep_p8_hold() -> None:
    material = _build_ready_cs12(mixed=True)

    assert material["blocker_question_need_observation_normalization_status_ref"] == cs.P7_R54_AHR_CS12_NORMALIZED_STATUS_REF
    assert material["question_need_observation_row_count"] == 24
    assert material["blocker_row_count"] == 3
    assert material["readfeel_blocker_row_count"] == 2
    assert material["execution_blocker_row_count"] == 1
    assert material["readfeel_blocker_observation_row_count"] == 2
    assert material["execution_blocker_observation_row_count"] == 1
    assert material["p5_repair_required_observation_row_count"] == 1
    assert material["emlis_readfeel_repair_required_row_count"] == 1
    assert material["readfeel_blocker_id_counts"][cs.P7_R54_AHR_CS08_READFEEL_BLOCKER_ID_OPTION_REFS[1]] == 1
    assert material["readfeel_blocker_id_counts"][cs.P7_R54_AHR_CS08_READFEEL_BLOCKER_ID_OPTION_REFS[0]] == 1
    assert material["execution_blocker_id_counts"][cs.P7_R54_AHR_CS08_EXECUTION_BLOCKER_ID_OPTION_REFS[0]] == 1
    assert material["question_need_primary_class_counts"]["question_may_reduce_overread_risk"] == 1
    assert material["question_need_primary_class_counts"]["not_question_emlis_readfeel_repair_required"] == 1
    assert material["question_need_primary_class_counts"]["insufficient_material_execution_blocker"] == 1
    assert material["p8_material_candidate_row_count"] == 0
    assert material["plus_single_question_candidate_row_count"] == 0
    assert material["premium_deep_dive_candidate_row_count"] == 0
    assert material["p8_start_allowed"] is False
    assert material["actual_review_evidence_complete"] is False
    assert cs.assert_p7_r54_ahr_cs12_blocker_question_need_observation_normalization_contract(material) is True


def test_cs12_blocks_rating_row_bodyfree_flag_violation() -> None:
    cs11 = _build_ready_cs11()
    cs11["rating_rows"][0]["question_text_included"] = True
    material = cs.build_p7_r54_ahr_cs12_blocker_question_need_observation_normalization(rating_row_normalization=cs11)

    assert material["blocker_question_need_observation_normalization_status_ref"] == cs.P7_R54_AHR_CS12_BLOCKED_STATUS_REF
    assert any("question_text_included" in blocker for blocker in material["execution_blocker_ids"])
    assert material["question_need_observation_rows"] == []
    assert cs.assert_p7_r54_ahr_cs12_blocker_question_need_observation_normalization_contract(material) is True


def test_cs12_sanitizes_p8_implementation_spec_flag_to_false() -> None:
    cs11 = _build_ready_cs11()
    cs11["rating_rows"][0]["plan_candidate_flags"]["p8_implementation_spec_finalized_here"] = True
    material = cs.build_p7_r54_ahr_cs12_blocker_question_need_observation_normalization(rating_row_normalization=cs11)

    assert material["blocker_question_need_observation_normalization_status_ref"] == cs.P7_R54_AHR_CS12_NORMALIZED_STATUS_REF
    assert material["p8_implementation_spec_finalized_here"] is False
    assert material["question_need_observation_rows"][0]["p8_implementation_spec_finalized_here"] is False
    assert material["question_need_observation_rows"][0]["plan_candidate_flags"]["p8_implementation_spec_finalized_here"] is False
    assert material["p8_start_allowed"] is False
    assert cs.assert_p7_r54_ahr_cs12_blocker_question_need_observation_normalization_contract(material) is True


def test_cs12_aliases_match_primary_builder_and_contract() -> None:
    primary = _build_ready_cs12()
    alias = cs.build_p7_r54_ahr_current_snapshot_actual_review_reentry_blocker_question_need_observation_normalization_bodyfree(
        rating_row_normalization=_build_ready_cs11()
    )

    assert alias == primary
    assert cs.assert_p7_r54_ahr_cs12_blocker_question_need_observation_normalization_bodyfree_contract(alias) is True
    assert (
        cs.assert_p7_r54_ahr_current_snapshot_actual_review_reentry_blocker_question_need_observation_normalization_bodyfree_contract(
            alias
        )
        is True
    )


def test_cs13_default_is_fail_closed_without_ready_cs12() -> None:
    material = cs.build_p7_r54_ahr_cs13_rating_question_consistency_guard()

    assert material["consistency_guard_status_ref"] == cs.P7_R54_AHR_CS13_BLOCKED_STATUS_REF
    assert material["rating_question_consistency_guard_passed"] is False
    assert material["pause_abort_expiration_disposal_receipt_allowed_next"] is False
    assert material["actual_question_need_observation_rows_materialized_here"] is False
    assert material["next_required_step"] == cs.P7_R54_AHR_CS13_BLOCKED_NEXT_REQUIRED_STEP_REF
    _assert_bodyfree_no_touch_allowing(material, ())
    assert cs.assert_p7_r54_ahr_cs13_rating_question_consistency_guard_contract(material) is True


def test_cs13_ready_guard_passes_bodyfree_without_promoting_later_phase() -> None:
    material = _build_ready_cs13()

    assert set(material) == set(cs.P7_R54_AHR_CS13_RATING_QUESTION_CONSISTENCY_GUARD_REQUIRED_FIELD_REFS)
    assert material["schema_version"] == cs.P7_R54_AHR_CS13_RATING_QUESTION_CONSISTENCY_GUARD_SCHEMA_VERSION
    assert material["policy_section"] == cs.P7_R54_AHR_CS13_STEP_REF
    assert material["operation_step_ref"] == cs.P7_R54_AHR_CS13_STEP_REF
    assert material["cs12_next_required_step"] == cs.P7_R54_AHR_CS13_STEP_REF
    assert material["current_basis_ref"] == cs.P7_R54_AHR_CS_ACTUAL_REVIEW_BASIS_REF
    assert material["historical_basis_ref"] == cs.P7_R54_AHR_CS_EXISTING_AHR_BASIS_REF
    assert material["consistency_guard_status_ref"] == cs.P7_R54_AHR_CS13_PASSED_STATUS_REF
    assert material["consistency_guard_reason_refs"] == [cs.P7_R54_AHR_CS13_READY_REASON_REF]
    assert material["question_need_observation_row_count"] == 24
    assert material["question_need_observation_row_ref_count"] == 24
    assert material["consistency_issue_rows"] == []
    assert material["consistency_issue_ids"] == []
    assert material["open_consistency_issue_count"] == 0
    assert material["rating_question_consistency_guard_passed"] is True
    assert material["question_text_absent"] is True
    assert material["draft_question_text_absent"] is True
    assert material["p8_implementation_spec_not_finalized_here"] is True
    assert material["p5_repair_rows_excluded_from_p8_material"] is True
    assert material["p4_current_surface_repair_rows_excluded_from_p8_material"] is True
    assert material["execution_blocker_rows_excluded_from_p8_material"] is True
    assert material["readfeel_blocker_rows_excluded_from_p8_material"] is True
    assert material["red_or_repair_rows_excluded_from_p8_material"] is True
    assert material["pause_abort_expiration_disposal_receipt_allowed_next"] is True
    assert material["actual_review_evidence_complete"] is False
    assert material["p8_start_allowed"] is False
    assert material["release_allowed"] is False
    assert tuple(material["implemented_steps"]) == cs.P7_R54_AHR_CS13_IMPLEMENTED_STEPS
    assert tuple(material["not_yet_implemented_steps"]) == cs.P7_R54_AHR_CS13_NOT_YET_IMPLEMENTED_STEPS
    assert material["next_required_step"] == cs.P7_R54_AHR_CS14_STEP_REF
    _assert_bodyfree_no_touch_allowing(material, cs.P7_R54_AHR_CS13_ALLOWED_TRUE_FALSE_FLAG_REFS)


def test_cs13_mixed_rows_pass_when_blockers_and_repairs_are_not_question_covered() -> None:
    material = _build_ready_cs13(mixed=True)

    assert material["consistency_guard_status_ref"] == cs.P7_R54_AHR_CS13_PASSED_STATUS_REF
    assert material["consistency_issue_rows"] == []
    assert material["consistency_issue_ids"] == []
    assert material["p8_material_candidate_row_count"] == 0
    assert material["p5_repair_required_observation_row_count"] == 1
    assert material["execution_blocker_observation_row_count"] == 1
    assert material["readfeel_blocker_observation_row_count"] == 2
    assert material["p8_start_allowed"] is False
    assert cs.assert_p7_r54_ahr_cs13_rating_question_consistency_guard_contract(material) is True


def test_cs13_blocks_execution_blocker_case_marked_as_p8_material_candidate() -> None:
    cs12 = _build_ready_cs12(mixed=True)
    mutated = deepcopy(cs12)
    target = next(row for row in mutated["question_need_observation_rows"] if row["execution_blocker_present"] is True)
    target["p8_design_material_candidate"] = True
    material = cs.build_p7_r54_ahr_cs13_rating_question_consistency_guard(
        blocker_question_need_observation_normalization=mutated
    )

    assert material["consistency_guard_status_ref"] == cs.P7_R54_AHR_CS13_BLOCKED_STATUS_REF
    assert "execution_blocker_routed_to_p8_material" in material["consistency_issue_ids"]
    assert material["consistency_issue_row_count"] >= 1
    assert material["pause_abort_expiration_disposal_receipt_allowed_next"] is False
    assert cs.assert_p7_r54_ahr_cs13_rating_question_consistency_guard_contract(material) is True


def test_cs13_blocks_repair_case_covered_by_question_candidate() -> None:
    cs12 = _build_ready_cs12(mixed=True)
    mutated = deepcopy(cs12)
    target = next(row for row in mutated["question_need_observation_rows"] if row["p5_repair_required"] is True)
    target["p8_design_material_candidate"] = True
    target["plus_single_question_candidate_later"] = True
    material = cs.build_p7_r54_ahr_cs13_rating_question_consistency_guard(
        blocker_question_need_observation_normalization=mutated
    )

    assert material["consistency_guard_status_ref"] == cs.P7_R54_AHR_CS13_BLOCKED_STATUS_REF
    assert "p5_repair_row_routed_to_p8_material" in material["consistency_issue_ids"]
    assert "repair_required_row_routed_to_p8_material" in material["consistency_issue_ids"]
    assert "p5_repair_primary_class_routed_to_question_candidate" in material["consistency_issue_ids"]
    assert cs.assert_p7_r54_ahr_cs13_rating_question_consistency_guard_contract(material) is True


def test_cs13_rejects_mutated_release_flag() -> None:
    material = _build_ready_cs13()
    mutated = deepcopy(material)
    mutated["p8_start_allowed"] = True

    with pytest.raises(ValueError):
        cs.assert_p7_r54_ahr_cs13_rating_question_consistency_guard_contract(mutated)


def test_cs13_aliases_match_primary_builder_and_contract() -> None:
    primary = _build_ready_cs13()
    alias = cs.build_p7_r54_ahr_current_snapshot_actual_review_reentry_rating_question_consistency_guard_bodyfree(
        blocker_question_need_observation_normalization=_build_ready_cs12()
    )

    assert alias == primary
    assert cs.assert_p7_r54_ahr_cs13_rating_question_consistency_guard_bodyfree_contract(alias) is True
    assert cs.assert_p7_r54_ahr_current_snapshot_actual_review_reentry_rating_question_consistency_guard_bodyfree_contract(alias) is True


@pytest.mark.parametrize(
    "promotion_flag",
    (
        "actual_review_evidence_complete",
        "disposal_receipt_materialized_here",
        "actual_disposal_receipt_materialized_here",
        "p5_confirmed_final",
        "p6_start_allowed",
        "p8_start_allowed",
        "p7_complete",
        "release_allowed",
        "actual_r52_reintake_execution_confirmed",
    ),
)
def test_cs12_cs13_do_not_promote_later_phase_or_release_flags(promotion_flag: str) -> None:
    cs12 = _build_ready_cs12(mixed=True)
    cs13 = _build_ready_cs13(mixed=True)

    assert cs12[promotion_flag] is False
    assert cs13[promotion_flag] is False
