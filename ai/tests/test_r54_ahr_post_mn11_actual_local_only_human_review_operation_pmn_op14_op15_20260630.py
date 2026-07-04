# -*- coding: utf-8 -*-
"""R54-AHR Post-MN11 actual local-only human review operation PMN-OP14/OP15 tests."""

from __future__ import annotations

from copy import deepcopy
from pathlib import Path
import sys

import pytest

TEST_DIR = Path(__file__).resolve().parent
if str(TEST_DIR) not in sys.path:
    sys.path.insert(0, str(TEST_DIR))

import emlis_ai_p7_r54_ahr_post_mn11_actual_local_only_human_review_operation_20260630 as pmn
import test_r54_ahr_post_mn11_actual_local_only_human_review_operation_pmn_op12_op13_20260630 as prev


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


def _contract_rows(op11: dict[str, object]) -> list[dict[str, object]]:
    return prev._contract_fixture_sanitized_review_result_rows(op11)


def _ready_op12_with_rows(rows: list[dict[str, object]], op11: dict[str, object] | None = None) -> dict[str, object]:
    actual_op11 = op11 or _ready_op11()
    return pmn.build_p7_r54_ahr_post_mn11_pmn_op12_sanitized_review_result_rows_intake_provenance_guard(
        actual_operation_receipt_intake=actual_op11,
        sanitized_review_result_rows_bodyfree=rows,
    )


def _ready_op12() -> dict[str, object]:
    return prev._ready_op12()


def _ready_op13(op12: dict[str, object] | None = None) -> dict[str, object]:
    return pmn.build_p7_r54_ahr_post_mn11_pmn_op13_rating_row_normalization_threshold_summary(
        sanitized_review_result_rows_intake=op12 or _ready_op12()
    )


def _ready_op14(op12: dict[str, object] | None = None, op13: dict[str, object] | None = None) -> dict[str, object]:
    source_op12 = op12 or _ready_op12()
    source_op13 = op13 or _ready_op13(source_op12)
    return pmn.build_p7_r54_ahr_post_mn11_pmn_op14_readfeel_label_connection_safe_display_blocker_classification(
        rating_row_normalization_threshold_summary=source_op13,
        sanitized_review_result_rows_intake=source_op12,
    )


def _ready_op15(op12: dict[str, object] | None = None, op14: dict[str, object] | None = None) -> dict[str, object]:
    source_op12 = op12 or _ready_op12()
    source_op14 = op14 or _ready_op14(source_op12)
    return pmn.build_p7_r54_ahr_post_mn11_pmn_op15_question_need_observation_row_normalization(
        readfeel_label_connection_safe_display_blocker_classification=source_op14,
        sanitized_review_result_rows_intake=source_op12,
    )


def _rows_with_plus_candidate(*, safe_display_risk: bool = False) -> tuple[dict[str, object], list[dict[str, object]]]:
    op11 = _ready_op11()
    rows = _contract_rows(op11)
    rows[0]["question_need_primary_class_ref"] = "plus_single_question_candidate_later"
    rows[0]["one_question_fit_ref"] = "fits_one_question"
    rows[0]["ambiguity_kind_refs"] = ["missing_target"]
    rows[0]["plan_candidate_flags"] = dict(rows[0]["plan_candidate_flags"])
    rows[0]["plan_candidate_flags"]["plus_single_question_candidate_later"] = True
    rows[0]["plan_candidate_flags"]["p8_design_material_candidate_only"] = True
    if safe_display_risk:
        rows[0]["safe_display_check_refs"] = list(rows[0]["safe_display_check_refs"]) + ["safe_display_risk_detected"]
        rows[0]["readfeel_blocker_ids"] = list(rows[0]["readfeel_blocker_ids"]) + ["safe_display_risk"]
        rows[0]["repair_required_refs"] = ["safe_display_repair_required"]
    return op11, rows


def test_pmn_op00_to_op13_implementation_is_present_before_op14_op15() -> None:
    op13 = _ready_op13()

    assert pmn.assert_p7_r54_ahr_post_mn11_pmn_op13_rating_row_normalization_threshold_summary_contract(op13) is True
    assert op13["next_required_step"] == pmn.P7_R54_AHR_POST_MN11_PMN_OP14_STEP_REF
    assert op13["rating_row_normalization_ready"] is True
    assert op13["question_need_observation_row_normalization_allowed_next"] is True
    assert tuple(op13["implemented_steps"]) == pmn.P7_R54_AHR_POST_MN11_PMN_OP13_IMPLEMENTED_STEPS
    assert tuple(op13["not_yet_implemented_steps"]) == pmn.P7_R54_AHR_POST_MN11_PMN_OP13_NOT_YET_IMPLEMENTED_STEPS
    _assert_bodyfree_no_touch_no_promotion(op13)


def test_pmn_op14_blocks_until_op13_and_op12_are_ready() -> None:
    blocked_op13 = pmn.build_p7_r54_ahr_post_mn11_pmn_op13_rating_row_normalization_threshold_summary(
        sanitized_review_result_rows_intake=pmn.build_p7_r54_ahr_post_mn11_pmn_op12_sanitized_review_result_rows_intake_provenance_guard(
            actual_operation_receipt_intake=_ready_op11()
        )
    )

    material = pmn.build_p7_r54_ahr_post_mn11_pmn_op14_readfeel_label_connection_safe_display_blocker_classification(
        rating_row_normalization_threshold_summary=blocked_op13
    )

    assert set(material) == set(pmn.P7_R54_AHR_POST_MN11_PMN_OP14_REQUIRED_FIELD_REFS)
    assert material["readfeel_label_connection_safe_display_blocker_classification_status_ref"] == pmn.P7_R54_AHR_POST_MN11_PMN_OP14_BLOCKED_STATUS_REF
    assert material["readfeel_label_connection_safe_display_blocker_classification_ready"] is False
    assert "pmn_op14_op13_rating_row_normalization_not_ready" in material["readfeel_label_connection_safe_display_blocker_classification_blocker_refs"]
    assert material["blocker_rows"] == []
    assert material["question_need_observation_normalization_allowed_next"] is False
    assert material["next_required_step"] == pmn.P7_R54_AHR_POST_MN11_PMN_OP14_BLOCKED_NEXT_REQUIRED_STEP_REF
    assert pmn.assert_p7_r54_ahr_post_mn11_pmn_op14_readfeel_label_connection_safe_display_blocker_classification_contract(material) is True
    _assert_bodyfree_no_touch_no_promotion(material)


def test_pmn_op14_classifies_clean_rating_material_without_p8_escape() -> None:
    material = _ready_op14()

    assert set(material) == set(pmn.P7_R54_AHR_POST_MN11_PMN_OP14_REQUIRED_FIELD_REFS)
    assert material["schema_version"] == pmn.P7_R54_AHR_POST_MN11_PMN_OP14_READFEEL_LABEL_CONNECTION_SAFE_DISPLAY_BLOCKER_CLASSIFICATION_SCHEMA_VERSION
    assert material["operation_step_ref"] == pmn.P7_R54_AHR_POST_MN11_PMN_OP14_STEP_REF
    assert material["readfeel_label_connection_safe_display_blocker_classification_status_ref"] == pmn.P7_R54_AHR_POST_MN11_PMN_OP14_READY_STATUS_REF
    assert material["readfeel_label_connection_safe_display_blocker_classification_ready"] is True
    assert material["readfeel_label_connection_safe_display_blocker_classification_blocker_refs"] == []
    assert tuple(material["readfeel_label_connection_safe_display_blocker_classification_reason_refs"]) == pmn.P7_R54_AHR_POST_MN11_PMN_OP14_READY_REASON_REFS
    assert tuple(material["blocker_row_required_field_refs"]) == pmn.P7_R54_AHR_POST_MN11_PMN_OP14_BLOCKER_ROW_REQUIRED_FIELD_REFS
    assert material["source_rating_row_count"] == 24
    assert material["source_review_result_row_count"] == 24
    assert material["case_ref_id_count"] == 24
    assert material["case_ref_ids_unique"] is True
    assert material["blocker_row_count"] == 0
    assert material["no_blocker_case_count"] == 24
    assert material["p5_repair_required_case_count"] == 0
    assert material["p4_current_only_repair_required_case_count"] == 0
    assert material["operation_blocked_case_count"] == 0
    assert material["safe_display_blocked_case_count"] == 0
    assert material["p8_material_candidate_case_count_bodyfree_only"] == 0
    assert material["p8_material_candidate_blocked_by_blocker_case_count"] == 0
    assert material["p5_p4_operation_readfeel_safe_display_blockers_not_escaped_to_p8_candidate"] is True
    assert material["safe_display_risk_not_question_candidate"] is True
    assert material["readfeel_label_connection_safe_display_blockers_classified_here"] is True
    assert material["actual_rating_rows_materialized_from_actual_rows"] is True
    assert material["actual_rating_rows_materialized_here"] is False
    assert material["actual_human_review_executed_by_person"] is True
    assert material["question_need_observation_normalization_allowed_next"] is True
    assert material["actual_question_need_observation_rows_materialized_here"] is False
    assert tuple(material["implemented_steps"]) == pmn.P7_R54_AHR_POST_MN11_PMN_OP14_IMPLEMENTED_STEPS
    assert tuple(material["not_yet_implemented_steps"]) == pmn.P7_R54_AHR_POST_MN11_PMN_OP14_NOT_YET_IMPLEMENTED_STEPS
    assert material["next_required_step"] == pmn.P7_R54_AHR_POST_MN11_PMN_OP15_STEP_REF
    assert pmn.assert_p7_r54_ahr_post_mn11_pmn_op14_readfeel_label_connection_safe_display_blocker_classification_contract(material) is True
    _assert_bodyfree_no_touch_no_promotion(material)


@pytest.mark.parametrize(
    ("field", "bad_value"),
    [
        ("readfeel_label_connection_safe_display_blocker_classification_ready", False),
        ("source_rating_row_count", 23),
        ("case_ref_ids_unique", False),
        ("p5_p4_operation_readfeel_safe_display_blockers_not_escaped_to_p8_candidate", False),
        ("safe_display_risk_not_question_candidate", False),
        ("actual_rating_rows_materialized_here", True),
        ("actual_question_need_observation_rows_materialized_here", True),
        ("question_need_observation_normalization_allowed_next", False),
        ("p8_start_allowed", True),
    ],
)
def test_pmn_op14_contract_rejects_classification_or_promotion_mutation(field: str, bad_value: object) -> None:
    material = _ready_op14()
    mutated = deepcopy(material)
    mutated[field] = bad_value

    with pytest.raises(ValueError):
        pmn.assert_p7_r54_ahr_post_mn11_pmn_op14_readfeel_label_connection_safe_display_blocker_classification_contract(mutated)


def test_pmn_op14_blocks_p8_candidate_when_safe_display_risk_exists() -> None:
    op11, rows = _rows_with_plus_candidate(safe_display_risk=True)
    op12 = _ready_op12_with_rows(rows, op11)
    op13 = _ready_op13(op12)
    material = _ready_op14(op12, op13)

    assert material["readfeel_label_connection_safe_display_blocker_classification_ready"] is True
    assert material["blocker_row_count"] >= 1
    assert material["safe_display_blocked_case_count"] == 1
    assert material["safe_display_blocker_row_count"] >= 1
    assert material["p8_material_candidate_case_count_bodyfree_only"] == 0
    assert material["p8_material_candidate_blocked_by_blocker_case_count"] == 1
    assert material["safe_display_risk_not_question_candidate"] is True
    assert any(row["blocker_category_ref"] == "p5_safe_display_risk" for row in material["blocker_rows"])
    for row in material["blocker_rows"]:
        assert row["schema_version"] == pmn.P7_R54_AHR_POST_MN11_PMN_OP14_BLOCKER_CLASSIFICATION_ROW_SCHEMA_VERSION
        assert row["body_free"] is True
        assert row["p8_material_candidate_blocked"] is True
        for false_flag in pmn.P7_R54_AHR_POST_MN11_PMN_OP14_BLOCKER_ROW_BODYFREE_FALSE_FLAG_REFS:
            assert row[false_flag] is False
    assert pmn.assert_p7_r54_ahr_post_mn11_pmn_op14_readfeel_label_connection_safe_display_blocker_classification_contract(material) is True
    _assert_bodyfree_no_touch_no_promotion(material)


def test_pmn_op15_blocks_until_op14_ready() -> None:
    material = pmn.build_p7_r54_ahr_post_mn11_pmn_op15_question_need_observation_row_normalization(
        readfeel_label_connection_safe_display_blocker_classification=pmn.build_p7_r54_ahr_post_mn11_pmn_op14_readfeel_label_connection_safe_display_blocker_classification()
    )

    assert set(material) == set(pmn.P7_R54_AHR_POST_MN11_PMN_OP15_REQUIRED_FIELD_REFS)
    assert material["question_need_observation_row_normalization_status_ref"] == pmn.P7_R54_AHR_POST_MN11_PMN_OP15_BLOCKED_STATUS_REF
    assert material["question_need_observation_row_normalization_ready"] is False
    assert "pmn_op15_op14_blocker_classification_not_ready" in material["question_need_observation_row_normalization_step_blocker_refs"]
    assert material["question_need_observation_rows"] == []
    assert material["question_need_observation_rows_normalized_here"] is False
    assert material["actual_question_need_observation_rows_materialized_from_actual_rows"] is False
    assert material["next_required_step"] == pmn.P7_R54_AHR_POST_MN11_PMN_OP15_BLOCKED_NEXT_REQUIRED_STEP_REF
    assert pmn.assert_p7_r54_ahr_post_mn11_pmn_op15_question_need_observation_row_normalization_contract(material) is True
    _assert_bodyfree_no_touch_no_promotion(material)


def test_pmn_op15_normalizes_question_need_observation_rows_without_question_text_or_p8_start() -> None:
    material = _ready_op15()

    assert set(material) == set(pmn.P7_R54_AHR_POST_MN11_PMN_OP15_REQUIRED_FIELD_REFS)
    assert material["schema_version"] == pmn.P7_R54_AHR_POST_MN11_PMN_OP15_QUESTION_NEED_OBSERVATION_ROW_NORMALIZATION_SCHEMA_VERSION
    assert material["operation_step_ref"] == pmn.P7_R54_AHR_POST_MN11_PMN_OP15_STEP_REF
    assert material["question_need_observation_row_normalization_status_ref"] == pmn.P7_R54_AHR_POST_MN11_PMN_OP15_READY_STATUS_REF
    assert material["question_need_observation_row_normalization_ready"] is True
    assert material["question_need_observation_row_normalization_step_blocker_refs"] == []
    assert tuple(material["question_need_observation_row_normalization_reason_refs"]) == pmn.P7_R54_AHR_POST_MN11_PMN_OP15_READY_REASON_REFS
    assert tuple(material["question_need_observation_row_required_field_refs"]) == pmn.P7_R54_AHR_POST_MN11_PMN_OP15_QUESTION_NEED_OBSERVATION_ROW_REQUIRED_FIELD_REFS
    assert material["source_sanitized_review_result_row_count"] == 24
    assert material["question_need_observation_row_count"] == 24
    assert material["question_need_observation_row_count_is_24"] is True
    assert material["case_ref_id_count"] == 24
    assert material["case_ref_ids_unique"] is True
    assert material["blind_case_id_count"] == 24
    assert material["blind_case_ids_unique"] is True
    assert material["packet_ref_id_count"] == 24
    assert material["packet_ref_ids_unique"] is True
    assert material["question_need_primary_class_counts"] == {"no_question_needed_emlis_can_observe": 24}
    assert material["one_question_fit_counts"] == {"not_needed": 24}
    assert material["p8_material_candidate_case_count_bodyfree_only"] == 0
    assert material["p8_material_candidate_blocked_by_blocker_case_count"] == 0
    assert material["question_text_materialized_here"] is False
    assert material["draft_question_text_materialized_here"] is False
    assert material["question_trigger_logic_materialized_here"] is False
    assert material["question_answer_storage_materialized_here"] is False
    assert material["p8_implementation_spec_finalized_here"] is False
    assert material["p8_start_allowed"] is False
    assert material["question_need_observation_rows_normalized_here"] is True
    assert material["actual_question_need_observation_rows_materialized_from_actual_rows"] is True
    assert material["actual_question_need_observation_rows_materialized_here"] is False
    assert material["actual_review_evidence_complete_from_real_review"] is False
    assert material["actual_review_evidence_complete_from_real_review_still_false"] is True
    assert tuple(material["implemented_steps"]) == pmn.P7_R54_AHR_POST_MN11_PMN_OP15_IMPLEMENTED_STEPS
    assert tuple(material["not_yet_implemented_steps"]) == pmn.P7_R54_AHR_POST_MN11_PMN_OP15_NOT_YET_IMPLEMENTED_STEPS
    assert material["next_required_step"] == pmn.P7_R54_AHR_POST_MN11_PMN_OP16_STEP_REF
    for row in material["question_need_observation_rows"]:
        assert row["schema_version"] == pmn.P7_R54_AHR_POST_MN11_PMN_OP15_QUESTION_NEED_OBSERVATION_ROW_SCHEMA_VERSION
        assert row["body_free"] is True
        assert row["question_text_materialized_here"] is False
        assert row["draft_question_text_materialized_here"] is False
        assert row["question_trigger_logic_materialized_here"] is False
        assert row["question_answer_storage_materialized_here"] is False
        assert row["p8_implementation_spec_finalized_here"] is False
        assert row["p8_start_allowed"] is False
        for false_flag in pmn.P7_R54_AHR_POST_MN11_PMN_OP15_QUESTION_OBSERVATION_ROW_BODYFREE_FALSE_FLAG_REFS:
            assert row[false_flag] is False
    assert pmn.assert_p7_r54_ahr_post_mn11_pmn_op15_question_need_observation_row_normalization_contract(material) is True
    _assert_bodyfree_no_touch_no_promotion(material)


def test_pmn_op15_allows_p8_material_candidate_only_without_start_when_no_blockers() -> None:
    op11, rows = _rows_with_plus_candidate(safe_display_risk=False)
    op12 = _ready_op12_with_rows(rows, op11)
    op14 = _ready_op14(op12)
    material = _ready_op15(op12, op14)

    assert op14["p8_material_candidate_case_count_bodyfree_only"] == 1
    assert material["question_need_observation_row_normalization_ready"] is True
    assert material["p8_material_candidate_case_count_bodyfree_only"] == 1
    assert material["plus_single_question_candidate_case_count_bodyfree_only"] == 1
    assert material["premium_deep_dive_candidate_case_count_bodyfree_only"] == 0
    assert material["p8_start_allowed"] is False
    candidate_rows = [row for row in material["question_need_observation_rows"] if row["p8_material_candidate_only"]]
    assert len(candidate_rows) == 1
    assert candidate_rows[0]["plus_single_question_candidate_later"] is True
    assert candidate_rows[0]["p8_start_allowed"] is False
    assert candidate_rows[0]["question_text_materialized_here"] is False
    assert pmn.assert_p7_r54_ahr_post_mn11_pmn_op15_question_need_observation_row_normalization_contract(material) is True
    _assert_bodyfree_no_touch_no_promotion(material)


def test_pmn_op15_blocks_p8_candidate_row_when_op14_classified_safe_display_blocker() -> None:
    op11, rows = _rows_with_plus_candidate(safe_display_risk=True)
    op12 = _ready_op12_with_rows(rows, op11)
    op14 = _ready_op14(op12)
    material = _ready_op15(op12, op14)

    assert op14["p8_material_candidate_case_count_bodyfree_only"] == 0
    assert op14["p8_material_candidate_blocked_by_blocker_case_count"] == 1
    assert material["question_need_observation_row_normalization_ready"] is True
    assert material["p8_material_candidate_case_count_bodyfree_only"] == 0
    assert material["p8_material_candidate_blocked_by_blocker_case_count"] == 1
    blocked_rows = [row for row in material["question_need_observation_rows"] if row["p8_material_candidate_blocked_by_blocker"]]
    assert len(blocked_rows) == 1
    assert blocked_rows[0]["p8_material_candidate_only"] is False
    assert blocked_rows[0]["p8_start_allowed"] is False
    assert blocked_rows[0]["question_text_materialized_here"] is False
    assert pmn.assert_p7_r54_ahr_post_mn11_pmn_op15_question_need_observation_row_normalization_contract(material) is True
    _assert_bodyfree_no_touch_no_promotion(material)


@pytest.mark.parametrize(
    ("field", "bad_value"),
    [
        ("question_need_observation_row_normalization_ready", False),
        ("question_need_observation_row_count", 23),
        ("question_text_materialized_here", True),
        ("draft_question_text_materialized_here", True),
        ("question_trigger_logic_materialized_here", True),
        ("question_answer_storage_materialized_here", True),
        ("p8_implementation_spec_finalized_here", True),
        ("p8_start_allowed", True),
        ("actual_question_need_observation_rows_materialized_here", True),
        ("actual_question_need_observation_rows_materialized_from_actual_rows", False),
        ("actual_review_evidence_complete_from_real_review", True),
    ],
)
def test_pmn_op15_contract_rejects_question_text_or_p8_promotion_mutation(field: str, bad_value: object) -> None:
    material = _ready_op15()
    mutated = deepcopy(material)
    mutated[field] = bad_value

    with pytest.raises(ValueError):
        pmn.assert_p7_r54_ahr_post_mn11_pmn_op15_question_need_observation_row_normalization_contract(mutated)


def test_pmn_op15_contract_rejects_row_level_question_text_or_p8_start_mutation() -> None:
    material = _ready_op15()
    mutated = deepcopy(material)
    mutated["question_need_observation_rows"][0]["question_text_materialized_here"] = True

    with pytest.raises(ValueError):
        pmn.assert_p7_r54_ahr_post_mn11_pmn_op15_question_need_observation_row_normalization_contract(mutated)


def test_pmn_op14_op15_aliases_match_primary_builders_and_contracts() -> None:
    op12 = _ready_op12()
    op13 = _ready_op13(op12)
    primary_op14 = pmn.build_p7_r54_ahr_post_mn11_pmn_op14_readfeel_label_connection_safe_display_blocker_classification(
        rating_row_normalization_threshold_summary=op13,
        sanitized_review_result_rows_intake=op12,
    )
    alias_op14 = pmn.build_p7_r54_ahr_post_mn11_actual_operation_readfeel_label_connection_safe_display_blocker_classification_bodyfree(
        rating_row_normalization_threshold_summary=op13,
        sanitized_review_result_rows_intake=op12,
    )
    assert alias_op14 == primary_op14
    assert pmn.assert_p7_r54_ahr_post_mn11_actual_operation_readfeel_label_connection_safe_display_blocker_classification_bodyfree_contract(alias_op14) is True

    primary_op15 = pmn.build_p7_r54_ahr_post_mn11_pmn_op15_question_need_observation_row_normalization(
        readfeel_label_connection_safe_display_blocker_classification=primary_op14,
        sanitized_review_result_rows_intake=op12,
    )
    alias_op15 = pmn.build_p7_r54_ahr_post_mn11_actual_operation_question_need_observation_row_normalization_bodyfree(
        readfeel_label_connection_safe_display_blocker_classification=primary_op14,
        sanitized_review_result_rows_intake=op12,
    )
    assert alias_op15 == primary_op15
    assert pmn.assert_p7_r54_ahr_post_mn11_actual_operation_question_need_observation_row_normalization_bodyfree_contract(alias_op15) is True
