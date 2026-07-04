# -*- coding: utf-8 -*-
"""R54-AHR Post-MN11 actual local-only human review operation PMN-OP20/OP21 tests."""

from __future__ import annotations

from copy import deepcopy
from pathlib import Path
import sys

import pytest

TEST_DIR = Path(__file__).resolve().parent
if str(TEST_DIR) not in sys.path:
    sys.path.insert(0, str(TEST_DIR))

import emlis_ai_p7_r54_ahr_post_mn11_actual_local_only_human_review_operation_20260630 as pmn
import test_r54_ahr_post_mn11_actual_local_only_human_review_operation_pmn_op18_op19_20260630 as prev


def _assert_bodyfree_no_touch_no_promotion(
    material: dict[str, object],
    *,
    allowed_true_false_flags: tuple[str, ...] = (),
) -> None:
    assert material["body_free"] is True
    allowed_true = set(allowed_true_false_flags)
    for key in pmn.P7_R54_AHR_POST_MN11_REQUIRED_FALSE_FLAG_REFS:
        if key in allowed_true:
            assert material[key] in (False, True), key
        else:
            assert material[key] is False, key
    for marker_map_key in ("public_contract", "post_mn11_no_touch_contract", "body_free_markers"):
        assert material[marker_map_key]
        assert all(value is False for value in material[marker_map_key].values()), marker_map_key
    for forbidden_key in pmn.P7_R54_AHR_POST_MN11_FORBIDDEN_PAYLOAD_KEY_REFS:
        assert forbidden_key not in material, forbidden_key
    if "not_claimed_boundary" in material:
        assert all(value is False for value in material["not_claimed_boundary"].values())


def _ready_bundle() -> tuple[dict[str, object], dict[str, object], dict[str, object], dict[str, object], dict[str, object], dict[str, object]]:
    op11, op12, op13, op15, op16, _op17, op18 = prev._ready_chain()
    op14 = prev._ready_op14(op12, op13)
    op19 = pmn.build_p7_r54_ahr_post_mn11_pmn_op19_actual_review_evidence_complete_predicate(
        final_no_body_no_question_no_path_no_hash_no_touch_validation=op18,
        actual_operation_receipt_intake=op11,
        sanitized_review_result_rows_intake=op12,
        rating_row_normalization_threshold_summary=op13,
        question_need_observation_row_normalization=op15,
        rating_question_consistency_guard=op16,
    )
    return op12, op14, op15, op16, op18, op19


def _ready_op20(
    op14: dict[str, object] | None = None,
    op15: dict[str, object] | None = None,
    op16: dict[str, object] | None = None,
    op19: dict[str, object] | None = None,
) -> dict[str, object]:
    _op12, source_op14, source_op15, source_op16, _op18, source_op19 = _ready_bundle()
    return pmn.build_p7_r54_ahr_post_mn11_pmn_op20_p5_p6_p8_r52_candidate_only_separation(
        actual_review_evidence_complete_predicate=op19 or source_op19,
        readfeel_label_connection_safe_display_blocker_classification=op14 or source_op14,
        question_need_observation_row_normalization=op15 or source_op15,
        rating_question_consistency_guard=op16 or source_op16,
    )


def _ready_op21(op20: dict[str, object] | None = None) -> dict[str, object]:
    return pmn.build_p7_r54_ahr_post_mn11_pmn_op21_existing_postcr22_ex07_ex18_reentry_mapping(
        p5_p6_p8_r52_candidate_only_separation=op20 or _ready_op20()
    )


def test_pmn_op00_to_op19_implementation_is_present_before_op20_op21() -> None:
    _op12, _op14, _op15, _op16, _op18, op19 = _ready_bundle()

    assert pmn.assert_p7_r54_ahr_post_mn11_pmn_op19_actual_review_evidence_complete_predicate_contract(op19) is True
    assert op19["actual_review_evidence_complete_predicate_passed"] is True
    assert op19["actual_review_evidence_complete_from_real_review"] is True
    assert op19["p5_final_allowed"] is False
    assert op19["p6_start_allowed"] is False
    assert op19["p8_start_allowed"] is False
    assert op19["actual_r52_reintake_execution_confirmed"] is False
    assert op19["next_required_step"] == pmn.P7_R54_AHR_POST_MN11_PMN_OP20_STEP_REF
    assert tuple(op19["implemented_steps"]) == pmn.P7_R54_AHR_POST_MN11_PMN_OP19_IMPLEMENTED_STEPS
    assert tuple(op19["not_yet_implemented_steps"]) == pmn.P7_R54_AHR_POST_MN11_PMN_OP19_NOT_YET_IMPLEMENTED_STEPS
    _assert_bodyfree_no_touch_no_promotion(
        op19,
        allowed_true_false_flags=pmn.P7_R54_AHR_POST_MN11_PMN_OP19_ALLOWED_TRUE_FALSE_FLAG_REFS,
    )


def test_pmn_op20_blocks_until_op19_and_candidate_material_are_ready() -> None:
    material = pmn.build_p7_r54_ahr_post_mn11_pmn_op20_p5_p6_p8_r52_candidate_only_separation()

    assert set(material) == set(pmn.P7_R54_AHR_POST_MN11_PMN_OP20_REQUIRED_FIELD_REFS)
    assert material["candidate_only_separation_status_ref"] == pmn.P7_R54_AHR_POST_MN11_PMN_OP20_BLOCKED_STATUS_REF
    assert material["candidate_only_separation_ready"] is False
    assert "pmn_op20_op19_actual_review_evidence_complete_predicate_missing" in material["candidate_only_separation_blocker_refs"]
    assert "pmn_op20_op14_blocker_classification_missing" in material["candidate_only_separation_blocker_refs"]
    assert material["actual_review_evidence_complete"] is False
    assert material["actual_review_evidence_complete_from_real_review"] is False
    assert material["p5_final_allowed"] is False
    assert material["p6_start_allowed"] is False
    assert material["p8_start_allowed"] is False
    assert material["next_required_step"] == pmn.P7_R54_AHR_POST_MN11_PMN_OP20_BLOCKED_NEXT_REQUIRED_STEP_REF
    assert pmn.assert_p7_r54_ahr_post_mn11_pmn_op20_p5_p6_p8_r52_candidate_only_separation_contract(material) is True
    _assert_bodyfree_no_touch_no_promotion(
        material,
        allowed_true_false_flags=pmn.P7_R54_AHR_POST_MN11_PMN_OP20_ALLOWED_TRUE_FALSE_FLAG_REFS,
    )


def test_pmn_op20_separates_p5_p6_r52_candidate_only_without_downstream_promotion() -> None:
    material = _ready_op20()

    assert set(material) == set(pmn.P7_R54_AHR_POST_MN11_PMN_OP20_REQUIRED_FIELD_REFS)
    assert material["schema_version"] == pmn.P7_R54_AHR_POST_MN11_PMN_OP20_P5_P6_P8_R52_CANDIDATE_ONLY_SEPARATION_SCHEMA_VERSION
    assert material["operation_step_ref"] == pmn.P7_R54_AHR_POST_MN11_PMN_OP20_STEP_REF
    assert material["candidate_only_separation_status_ref"] == pmn.P7_R54_AHR_POST_MN11_PMN_OP20_READY_STATUS_REF
    assert material["candidate_only_separation_ready"] is True
    assert material["candidate_only_separation_blocker_refs"] == []
    assert material["actual_review_evidence_complete"] is True
    assert material["actual_review_evidence_complete_from_real_review"] is True
    assert material["p5_confirmed_candidate_bodyfree_only"] is True
    assert material["p5_confirmed_candidate_case_count"] == 24
    assert material["p6_limited_human_readfeel_candidate_only"] is True
    assert material["r52_reintake_handoff_candidate_only"] is True
    assert material["r52_reintake_handoff_candidate_case_count"] == 24
    assert material["p8_question_need_observation_material_candidate_only"] is False
    assert material["p8_material_candidate_case_count_bodyfree_only"] == 0
    assert "P5_CONFIRMED_CANDIDATE_BODYFREE_ONLY" in material["selected_decision_refs"]
    assert "P6_LIMITED_HUMAN_READFEEL_CANDIDATE_ONLY" in material["selected_decision_refs"]
    assert "R52_REINTAKE_HANDOFF_CANDIDATE_ONLY" in material["selected_decision_refs"]
    assert material["candidate_only_separation_does_not_finalize_p5"] is True
    assert material["candidate_only_separation_does_not_start_p6"] is True
    assert material["candidate_only_separation_does_not_start_p8"] is True
    assert material["candidate_only_separation_does_not_execute_r52"] is True
    assert material["candidate_only_separation_does_not_complete_p7_or_release"] is True
    assert material["p5_final_allowed"] is False
    assert material["p6_start_allowed"] is False
    assert material["p8_start_allowed"] is False
    assert material["actual_r52_reintake_execution_confirmed"] is False
    assert material["p7_complete"] is False
    assert material["release_allowed"] is False
    assert tuple(material["implemented_steps"]) == pmn.P7_R54_AHR_POST_MN11_PMN_OP20_IMPLEMENTED_STEPS
    assert tuple(material["not_yet_implemented_steps"]) == pmn.P7_R54_AHR_POST_MN11_PMN_OP20_NOT_YET_IMPLEMENTED_STEPS
    assert material["next_required_step"] == pmn.P7_R54_AHR_POST_MN11_PMN_OP21_STEP_REF
    assert pmn.assert_p7_r54_ahr_post_mn11_pmn_op20_p5_p6_p8_r52_candidate_only_separation_contract(material) is True
    _assert_bodyfree_no_touch_no_promotion(
        material,
        allowed_true_false_flags=pmn.P7_R54_AHR_POST_MN11_PMN_OP20_ALLOWED_TRUE_FALSE_FLAG_REFS,
    )


@pytest.mark.parametrize(
    ("field", "bad_value"),
    [
        ("candidate_only_separation_ready", False),
        ("actual_review_evidence_complete", False),
        ("actual_review_evidence_complete_from_real_review", False),
        ("candidate_only_separation_does_not_start_p8", False),
        ("p5_final_allowed", True),
        ("p6_start_allowed", True),
        ("p8_start_allowed", True),
        ("actual_r52_reintake_execution_confirmed", True),
        ("release_allowed", True),
    ],
)
def test_pmn_op20_contract_rejects_candidate_or_promotion_mutation(field: str, bad_value: object) -> None:
    material = _ready_op20()
    mutated = deepcopy(material)
    mutated[field] = bad_value

    with pytest.raises(ValueError):
        pmn.assert_p7_r54_ahr_post_mn11_pmn_op20_p5_p6_p8_r52_candidate_only_separation_contract(mutated)


def test_pmn_op21_blocks_until_op20_candidate_only_separation_is_ready() -> None:
    material = pmn.build_p7_r54_ahr_post_mn11_pmn_op21_existing_postcr22_ex07_ex18_reentry_mapping()

    assert set(material) == set(pmn.P7_R54_AHR_POST_MN11_PMN_OP21_REQUIRED_FIELD_REFS)
    assert material["existing_postcr22_ex07_ex18_reentry_mapping_status_ref"] == pmn.P7_R54_AHR_POST_MN11_PMN_OP21_BLOCKED_STATUS_REF
    assert material["existing_postcr22_ex07_ex18_reentry_mapping_ready"] is False
    assert "pmn_op21_candidate_only_separation_missing" in material["existing_postcr22_ex07_ex18_reentry_mapping_blocker_refs"]
    assert material["reentry_mapping_rows"] == []
    assert material["reentry_executed_here"] is False
    assert material["actual_review_evidence_complete"] is False
    assert material["next_required_step"] == pmn.P7_R54_AHR_POST_MN11_PMN_OP21_BLOCKED_NEXT_REQUIRED_STEP_REF
    assert pmn.assert_p7_r54_ahr_post_mn11_pmn_op21_existing_postcr22_ex07_ex18_reentry_mapping_contract(material) is True
    _assert_bodyfree_no_touch_no_promotion(
        material,
        allowed_true_false_flags=pmn.P7_R54_AHR_POST_MN11_PMN_OP21_ALLOWED_TRUE_FALSE_FLAG_REFS,
    )


def test_pmn_op21_maps_to_existing_postcr22_ex07_to_ex18_without_executing_reentry_or_promotion() -> None:
    op20 = _ready_op20()
    material = _ready_op21(op20)

    assert set(material) == set(pmn.P7_R54_AHR_POST_MN11_PMN_OP21_REQUIRED_FIELD_REFS)
    assert material["schema_version"] == pmn.P7_R54_AHR_POST_MN11_PMN_OP21_EXISTING_POSTCR22_EX07_EX18_REENTRY_MAPPING_SCHEMA_VERSION
    assert material["operation_step_ref"] == pmn.P7_R54_AHR_POST_MN11_PMN_OP21_STEP_REF
    assert material["existing_postcr22_ex07_ex18_reentry_mapping_status_ref"] == pmn.P7_R54_AHR_POST_MN11_PMN_OP21_READY_STATUS_REF
    assert material["existing_postcr22_ex07_ex18_reentry_mapping_ready"] is True
    assert material["existing_postcr22_ex07_ex18_reentry_mapping_blocker_refs"] == []
    assert material["reentry_mapping_row_count"] == 12
    assert material["existing_ex_line_reentry_first_step_ref"] == pmn.ex.P7_R54_AHR_POST_CR22_EX07_STEP_REF
    assert material["existing_ex_line_reentry_last_step_ref"] == pmn.ex.P7_R54_AHR_POST_CR22_EX18_STEP_REF
    assert tuple(material["existing_ex_line_reentry_step_refs"]) == pmn.P7_R54_AHR_POST_MN11_EXISTING_EX_LINE_REENTRY_STEP_REFS
    assert tuple(material["existing_ex_line_reentry_role_refs"]) == pmn.P7_R54_AHR_POST_MN11_EXISTING_EX_LINE_REENTRY_ROLE_REFS
    assert all(row["body_free"] is True for row in material["reentry_mapping_rows"])
    assert all(row["reentry_executed_here"] is False for row in material["reentry_mapping_rows"])
    assert all(row["existing_helper_reused"] is True for row in material["reentry_mapping_rows"])
    assert material["postcr22_ex07_ex18_reentry_executed_here"] is False
    assert material["reentry_executed_here"] is False
    assert material["reentry_mapping_reuses_existing_postcr22_ex_line"] is True
    assert material["reentry_mapping_does_not_reimplement_ex_helpers"] is True
    assert material["reentry_mapping_does_not_execute_ex_helpers_here"] is True
    assert material["postcr22_ex18_ready_is_manual_hold_not_r52_execution"] is True
    assert material["new_giant_wrapper_required"] is False
    assert material["actual_review_evidence_complete"] is True
    assert material["actual_review_evidence_complete_from_real_review"] is True
    assert material["p5_final_allowed"] is False
    assert material["p6_start_allowed"] is False
    assert material["p8_start_allowed"] is False
    assert material["r52_reintake_execution_started_here"] is False
    assert material["actual_r52_reintake_execution_confirmed"] is False
    assert material["p7_complete"] is False
    assert material["release_allowed"] is False
    assert tuple(material["implemented_steps"]) == pmn.P7_R54_AHR_POST_MN11_PMN_OP21_IMPLEMENTED_STEPS
    assert tuple(material["not_yet_implemented_steps"]) == pmn.P7_R54_AHR_POST_MN11_PMN_OP21_NOT_YET_IMPLEMENTED_STEPS
    assert material["next_required_step"] == pmn.P7_R54_AHR_POST_MN11_PMN_OP22_STEP_REF
    assert pmn.assert_p7_r54_ahr_post_mn11_pmn_op21_existing_postcr22_ex07_ex18_reentry_mapping_contract(material) is True
    _assert_bodyfree_no_touch_no_promotion(
        material,
        allowed_true_false_flags=pmn.P7_R54_AHR_POST_MN11_PMN_OP21_ALLOWED_TRUE_FALSE_FLAG_REFS,
    )


@pytest.mark.parametrize(
    ("field", "bad_value"),
    [
        ("existing_postcr22_ex07_ex18_reentry_mapping_ready", False),
        ("reentry_executed_here", True),
        ("postcr22_ex07_ex18_reentry_executed_here", True),
        ("actual_review_evidence_complete", False),
        ("actual_review_evidence_complete_from_real_review", False),
        ("reentry_mapping_does_not_execute_ex_helpers_here", False),
        ("p5_final_allowed", True),
        ("p8_start_allowed", True),
        ("r52_reintake_execution_started_here", True),
        ("release_allowed", True),
    ],
)
def test_pmn_op21_contract_rejects_reentry_or_promotion_mutation(field: str, bad_value: object) -> None:
    material = _ready_op21()
    mutated = deepcopy(material)
    mutated[field] = bad_value

    with pytest.raises(ValueError):
        pmn.assert_p7_r54_ahr_post_mn11_pmn_op21_existing_postcr22_ex07_ex18_reentry_mapping_contract(mutated)


def test_pmn_op20_op21_aliases_match_primary_builders_and_contracts() -> None:
    _op12, op14, op15, op16, _op18, op19 = _ready_bundle()
    primary_op20 = _ready_op20(op14, op15, op16, op19)
    alias_op20 = pmn.build_p7_r54_ahr_post_mn11_actual_operation_p5_p6_p8_r52_candidate_only_separation_bodyfree(
        actual_review_evidence_complete_predicate=op19,
        readfeel_label_connection_safe_display_blocker_classification=op14,
        question_need_observation_row_normalization=op15,
        rating_question_consistency_guard=op16,
    )
    assert alias_op20 == primary_op20
    assert pmn.assert_p7_r54_ahr_post_mn11_actual_operation_p5_p6_p8_r52_candidate_only_separation_bodyfree_contract(alias_op20) is True

    primary_op21 = _ready_op21(primary_op20)
    alias_op21 = pmn.build_p7_r54_ahr_post_mn11_actual_operation_existing_postcr22_ex07_ex18_reentry_mapping_bodyfree(
        p5_p6_p8_r52_candidate_only_separation=primary_op20
    )
    assert alias_op21 == primary_op21
    assert pmn.assert_p7_r54_ahr_post_mn11_actual_operation_existing_postcr22_ex07_ex18_reentry_mapping_bodyfree_contract(alias_op21) is True
