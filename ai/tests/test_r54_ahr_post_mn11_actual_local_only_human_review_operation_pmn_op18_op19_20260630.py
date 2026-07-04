# -*- coding: utf-8 -*-
"""R54-AHR Post-MN11 actual local-only human review operation PMN-OP18/OP19 tests."""

from __future__ import annotations

from copy import deepcopy
from pathlib import Path
import sys

import pytest

TEST_DIR = Path(__file__).resolve().parent
if str(TEST_DIR) not in sys.path:
    sys.path.insert(0, str(TEST_DIR))

import emlis_ai_p7_r54_ahr_post_mn11_actual_local_only_human_review_operation_20260630 as pmn
import test_r54_ahr_post_mn11_actual_local_only_human_review_operation_pmn_op12_op13_20260630 as op12_prev
import test_r54_ahr_post_mn11_actual_local_only_human_review_operation_pmn_op16_op17_20260630 as prev


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


def _ready_op11() -> dict[str, object]:
    return op12_prev._ready_op11()


def _ready_op12() -> dict[str, object]:
    return prev._ready_op12()


def _ready_op13(op12: dict[str, object] | None = None) -> dict[str, object]:
    source_op12 = op12 or _ready_op12()
    return prev._ready_op13(source_op12)


def _ready_op14(
    op12: dict[str, object] | None = None,
    op13: dict[str, object] | None = None,
) -> dict[str, object]:
    source_op12 = op12 or _ready_op12()
    source_op13 = op13 or _ready_op13(source_op12)
    return prev._ready_op14(source_op12, source_op13)


def _ready_op15(
    op12: dict[str, object] | None = None,
    op14: dict[str, object] | None = None,
) -> dict[str, object]:
    source_op12 = op12 or _ready_op12()
    source_op14 = op14 or _ready_op14(source_op12)
    return prev._ready_op15(source_op12, source_op14)


def _ready_op16(
    op12: dict[str, object] | None = None,
    op13: dict[str, object] | None = None,
    op14: dict[str, object] | None = None,
    op15: dict[str, object] | None = None,
) -> dict[str, object]:
    source_op12 = op12 or _ready_op12()
    source_op13 = op13 or _ready_op13(source_op12)
    source_op14 = op14 or _ready_op14(source_op12, source_op13)
    source_op15 = op15 or _ready_op15(source_op12, source_op14)
    return prev._ready_op16(source_op12, source_op13, source_op14, source_op15)


def _ready_op17(op16: dict[str, object] | None = None) -> dict[str, object]:
    source_op16 = op16 or _ready_op16()
    return prev._ready_op17(source_op16)


def _ready_chain() -> tuple[dict[str, object], dict[str, object], dict[str, object], dict[str, object], dict[str, object], dict[str, object], dict[str, object]]:
    op11 = _ready_op11()
    op12 = _ready_op12()
    op13 = _ready_op13(op12)
    op14 = _ready_op14(op12, op13)
    op15 = _ready_op15(op12, op14)
    op16 = _ready_op16(op12, op13, op14, op15)
    op17 = _ready_op17(op16)
    return op11, op12, op13, op15, op16, op17, _ready_op18(op11, op12, op13, op15, op16, op17)


def _ready_op18(
    op11: dict[str, object] | None = None,
    op12: dict[str, object] | None = None,
    op13: dict[str, object] | None = None,
    op15: dict[str, object] | None = None,
    op16: dict[str, object] | None = None,
    op17: dict[str, object] | None = None,
    *,
    bodyfree_artifacts: list[object] | None = None,
) -> dict[str, object]:
    source_op11 = op11 or _ready_op11()
    source_op12 = op12 or _ready_op12()
    source_op13 = op13 or _ready_op13(source_op12)
    source_op15 = op15 or _ready_op15(source_op12)
    source_op16 = op16 or _ready_op16(source_op12, source_op13, None, source_op15)
    source_op17 = op17 or _ready_op17(source_op16)
    artifacts = bodyfree_artifacts if bodyfree_artifacts is not None else [
        source_op11,
        source_op12,
        source_op13,
        source_op15,
        source_op16,
        source_op17,
    ]
    return pmn.build_p7_r54_ahr_post_mn11_pmn_op18_final_no_body_no_question_no_path_no_hash_no_touch_validation(
        disposal_purge_receipt_intake=source_op17,
        bodyfree_artifacts=artifacts,
    )


def test_pmn_op00_to_op17_implementation_is_present_before_op18_op19() -> None:
    op17 = _ready_op17()

    assert pmn.assert_p7_r54_ahr_post_mn11_pmn_op17_disposal_purge_receipt_intake_contract(op17) is True
    assert op17["disposal_purge_receipt_intake_ready"] is True
    assert op17["disposal_purge_receipt_accepted"] is True
    assert op17["next_required_step"] == pmn.P7_R54_AHR_POST_MN11_PMN_OP18_STEP_REF
    assert tuple(op17["implemented_steps"]) == pmn.P7_R54_AHR_POST_MN11_PMN_OP17_IMPLEMENTED_STEPS
    assert tuple(op17["not_yet_implemented_steps"]) == pmn.P7_R54_AHR_POST_MN11_PMN_OP17_NOT_YET_IMPLEMENTED_STEPS
    _assert_bodyfree_no_touch_no_promotion(op17)


def test_pmn_op18_blocks_until_op17_disposal_receipt_and_artifacts_are_ready() -> None:
    material = pmn.build_p7_r54_ahr_post_mn11_pmn_op18_final_no_body_no_question_no_path_no_hash_no_touch_validation()

    assert set(material) == set(pmn.P7_R54_AHR_POST_MN11_PMN_OP18_REQUIRED_FIELD_REFS)
    assert material["final_no_leak_validation_status_ref"] == pmn.P7_R54_AHR_POST_MN11_PMN_OP18_BLOCKED_STATUS_REF
    assert material["final_no_leak_validation_evaluated"] is False
    assert material["final_no_leak_validation_passed"] is False
    assert "pmn_op18_op17_disposal_purge_receipt_not_accepted" in material["final_no_leak_validation_step_blocker_refs"]
    assert material["disposal_verified"] is False
    assert material["actual_review_evidence_complete_from_real_review"] is False
    assert material["next_required_step"] == pmn.P7_R54_AHR_POST_MN11_PMN_OP18_BLOCKED_NEXT_REQUIRED_STEP_REF
    assert pmn.assert_p7_r54_ahr_post_mn11_pmn_op18_final_no_body_no_question_no_path_no_hash_no_touch_validation_contract(material) is True
    _assert_bodyfree_no_touch_no_promotion(material)


def test_pmn_op18_passes_final_no_leak_validation_and_verifies_disposal_without_completing_evidence() -> None:
    material = _ready_op18()

    assert set(material) == set(pmn.P7_R54_AHR_POST_MN11_PMN_OP18_REQUIRED_FIELD_REFS)
    assert material["schema_version"] == pmn.P7_R54_AHR_POST_MN11_PMN_OP18_FINAL_NO_BODY_NO_QUESTION_NO_PATH_NO_HASH_NO_TOUCH_VALIDATION_SCHEMA_VERSION
    assert material["operation_step_ref"] == pmn.P7_R54_AHR_POST_MN11_PMN_OP18_STEP_REF
    assert material["final_no_leak_validation_status_ref"] == pmn.P7_R54_AHR_POST_MN11_PMN_OP18_READY_STATUS_REF
    assert material["final_no_leak_validation_evaluated"] is True
    assert material["final_no_leak_validation_passed"] is True
    assert material["final_no_leak_validation_step_blocker_refs"] == []
    assert material["forbidden_payload_key_paths"] == []
    assert material["body_leak_refs"] == []
    assert material["question_text_leak_refs"] == []
    assert material["path_or_hash_leak_refs"] == []
    assert material["terminal_output_leak_refs"] == []
    assert material["no_touch_contract_mutation_refs"] == []
    assert material["no_body_leak_validation_passed"] is True
    assert material["no_question_text_validation_passed"] is True
    assert material["no_path_hash_validation_passed"] is True
    assert material["no_terminal_output_body_validation_passed"] is True
    assert material["no_touch_validation_passed"] is True
    assert material["disposal_verified"] is True
    assert "disposal_verified_only_after_final_no_leak_validation" in material["final_no_leak_validation_reason_refs"]
    assert material["actual_review_evidence_complete"] is False
    assert material["actual_review_evidence_complete_from_real_review"] is False
    assert tuple(material["implemented_steps"]) == pmn.P7_R54_AHR_POST_MN11_PMN_OP18_IMPLEMENTED_STEPS
    assert tuple(material["not_yet_implemented_steps"]) == pmn.P7_R54_AHR_POST_MN11_PMN_OP18_NOT_YET_IMPLEMENTED_STEPS
    assert material["next_required_step"] == pmn.P7_R54_AHR_POST_MN11_PMN_OP19_STEP_REF
    assert pmn.assert_p7_r54_ahr_post_mn11_pmn_op18_final_no_body_no_question_no_path_no_hash_no_touch_validation_contract(material) is True
    _assert_bodyfree_no_touch_no_promotion(material, allowed_true_false_flags=("disposal_verified",))


def test_pmn_op18_detects_body_question_path_hash_terminal_and_no_touch_leak() -> None:
    op11, op12, op13, op15, op16, op17, _ = _ready_chain()
    leaked = deepcopy(op12)
    leaked["question_text"] = "must not be stored"
    leaked["local_absolute_path_included"] = True
    leaked["terminal_output_body_included"] = True
    leaked["public_contract"] = {**leaked["public_contract"], "api_changed": True}
    material = _ready_op18(
        op11,
        op12,
        op13,
        op15,
        op16,
        op17,
        bodyfree_artifacts=[op11, leaked, op17],
    )

    assert material["final_no_leak_validation_status_ref"] == pmn.P7_R54_AHR_POST_MN11_PMN_OP18_FAILED_STATUS_REF
    assert material["final_no_leak_validation_evaluated"] is True
    assert material["final_no_leak_validation_passed"] is False
    assert material["no_question_text_validation_passed"] is False
    assert material["no_path_hash_validation_passed"] is False
    assert material["no_terminal_output_body_validation_passed"] is False
    assert material["no_touch_validation_passed"] is False
    assert material["question_text_leak_refs"]
    assert material["path_or_hash_leak_refs"]
    assert material["terminal_output_leak_refs"]
    assert material["no_touch_contract_mutation_refs"]
    assert material["forbidden_payload_key_paths"]
    assert material["disposal_verified"] is False
    assert material["actual_review_evidence_complete_from_real_review"] is False
    assert material["next_required_step"] == pmn.P7_R54_AHR_POST_MN11_PMN_OP18_BLOCKED_NEXT_REQUIRED_STEP_REF
    assert pmn.assert_p7_r54_ahr_post_mn11_pmn_op18_final_no_body_no_question_no_path_no_hash_no_touch_validation_contract(material) is True
    _assert_bodyfree_no_touch_no_promotion(material)


@pytest.mark.parametrize(
    ("field", "bad_value"),
    [
        ("final_no_leak_validation_passed", False),
        ("no_body_leak_validation_passed", False),
        ("no_question_text_validation_passed", False),
        ("no_path_hash_validation_passed", False),
        ("no_touch_validation_passed", False),
        ("actual_review_evidence_complete", True),
        ("actual_review_evidence_complete_from_real_review", True),
        ("p8_start_allowed", True),
    ],
)
def test_pmn_op18_contract_rejects_validation_or_promotion_mutation(field: str, bad_value: object) -> None:
    material = _ready_op18()
    mutated = deepcopy(material)
    mutated[field] = bad_value

    with pytest.raises(ValueError):
        pmn.assert_p7_r54_ahr_post_mn11_pmn_op18_final_no_body_no_question_no_path_no_hash_no_touch_validation_contract(mutated)


def test_pmn_op19_blocks_as_incomplete_until_upstream_evidence_bundle_is_supplied() -> None:
    material = pmn.build_p7_r54_ahr_post_mn11_pmn_op19_actual_review_evidence_complete_predicate()

    assert set(material) == set(pmn.P7_R54_AHR_POST_MN11_PMN_OP19_REQUIRED_FIELD_REFS)
    assert material["actual_review_evidence_complete_predicate_status_ref"] == pmn.P7_R54_AHR_POST_MN11_PMN_OP19_BLOCKED_STATUS_REF
    assert material["actual_review_evidence_complete_predicate_passed"] is False
    assert material["actual_review_evidence_complete"] is False
    assert material["actual_review_evidence_complete_from_real_review"] is False
    assert "pmn_op19_op11_actual_operation_receipt_missing" in material["actual_review_evidence_complete_predicate_blocker_refs"]
    assert "pmn_op19_op18_final_no_leak_validation_not_passed" in material["actual_review_evidence_complete_predicate_blocker_refs"]
    assert material["next_required_step"] == pmn.P7_R54_AHR_POST_MN11_PMN_OP19_BLOCKED_NEXT_REQUIRED_STEP_REF
    assert pmn.assert_p7_r54_ahr_post_mn11_pmn_op19_actual_review_evidence_complete_predicate_contract(material) is True
    _assert_bodyfree_no_touch_no_promotion(material, allowed_true_false_flags=pmn.P7_R54_AHR_POST_MN11_PMN_OP19_ALLOWED_TRUE_FALSE_FLAG_REFS)


def test_pmn_op19_completes_predicate_from_bodyfree_actual_evidence_without_downstream_promotion() -> None:
    op11, op12, op13, op15, op16, _op17, op18 = _ready_chain()
    material = pmn.build_p7_r54_ahr_post_mn11_pmn_op19_actual_review_evidence_complete_predicate(
        final_no_body_no_question_no_path_no_hash_no_touch_validation=op18,
        actual_operation_receipt_intake=op11,
        sanitized_review_result_rows_intake=op12,
        rating_row_normalization_threshold_summary=op13,
        question_need_observation_row_normalization=op15,
        rating_question_consistency_guard=op16,
    )

    assert set(material) == set(pmn.P7_R54_AHR_POST_MN11_PMN_OP19_REQUIRED_FIELD_REFS)
    assert material["schema_version"] == pmn.P7_R54_AHR_POST_MN11_PMN_OP19_ACTUAL_REVIEW_EVIDENCE_COMPLETE_PREDICATE_SCHEMA_VERSION
    assert material["operation_step_ref"] == pmn.P7_R54_AHR_POST_MN11_PMN_OP19_STEP_REF
    assert material["actual_review_evidence_complete_predicate_status_ref"] == pmn.P7_R54_AHR_POST_MN11_PMN_OP19_READY_STATUS_REF
    assert material["actual_review_evidence_complete_predicate_passed"] is True
    assert material["actual_review_evidence_complete_predicate_blocker_refs"] == []
    assert material["actual_source_guard_passed"] is True
    assert material["actual_human_review_executed_by_person"] is True
    assert material["reviewed_case_count"] == 24
    assert material["selection_row_count"] == 24
    assert material["sanitized_review_result_row_count"] == 24
    assert material["rating_row_count"] == 24
    assert material["question_need_observation_row_count"] == 24
    assert material["disposal_verified"] is True
    assert material["no_body_leak_validation_passed"] is True
    assert material["no_question_text_validation_passed"] is True
    assert material["no_path_hash_validation_passed"] is True
    assert material["no_touch_validation_passed"] is True
    assert material["consistency_guard_passed"] is True
    assert material["actual_review_evidence_complete"] is True
    assert material["actual_review_evidence_complete_from_real_review"] is True
    assert material["downstream_manual_decision_hold_required"] is True
    assert material["p5_final_allowed"] is False
    assert material["p6_start_allowed"] is False
    assert material["p8_start_allowed"] is False
    assert material["actual_r52_reintake_execution_confirmed"] is False
    assert material["p7_complete"] is False
    assert material["release_allowed"] is False
    assert tuple(material["implemented_steps"]) == pmn.P7_R54_AHR_POST_MN11_PMN_OP19_IMPLEMENTED_STEPS
    assert tuple(material["not_yet_implemented_steps"]) == pmn.P7_R54_AHR_POST_MN11_PMN_OP19_NOT_YET_IMPLEMENTED_STEPS
    assert material["next_required_step"] == pmn.P7_R54_AHR_POST_MN11_PMN_OP20_STEP_REF
    assert pmn.assert_p7_r54_ahr_post_mn11_pmn_op19_actual_review_evidence_complete_predicate_contract(material) is True
    _assert_bodyfree_no_touch_no_promotion(
        material,
        allowed_true_false_flags=pmn.P7_R54_AHR_POST_MN11_PMN_OP19_ALLOWED_TRUE_FALSE_FLAG_REFS,
    )


def test_pmn_op19_remains_incomplete_when_final_validation_failed() -> None:
    op11, op12, op13, op15, op16, op17, _ = _ready_chain()
    leaked = deepcopy(op12)
    leaked["question_text"] = "must not be stored"
    op18_failed = _ready_op18(
        op11,
        op12,
        op13,
        op15,
        op16,
        op17,
        bodyfree_artifacts=[leaked, op17],
    )
    material = pmn.build_p7_r54_ahr_post_mn11_pmn_op19_actual_review_evidence_complete_predicate(
        final_no_body_no_question_no_path_no_hash_no_touch_validation=op18_failed,
        actual_operation_receipt_intake=op11,
        sanitized_review_result_rows_intake=op12,
        rating_row_normalization_threshold_summary=op13,
        question_need_observation_row_normalization=op15,
        rating_question_consistency_guard=op16,
    )

    assert material["actual_review_evidence_complete_predicate_status_ref"] == pmn.P7_R54_AHR_POST_MN11_PMN_OP19_BLOCKED_STATUS_REF
    assert material["actual_review_evidence_complete_predicate_passed"] is False
    assert "pmn_op19_op18_final_no_leak_validation_not_passed" in material["actual_review_evidence_complete_predicate_blocker_refs"]
    assert "pmn_op19_no_question_text_validation_not_passed" in material["actual_review_evidence_complete_predicate_blocker_refs"]
    assert material["actual_review_evidence_complete"] is False
    assert material["actual_review_evidence_complete_from_real_review"] is False
    assert material["next_required_step"] == pmn.P7_R54_AHR_POST_MN11_PMN_OP19_BLOCKED_NEXT_REQUIRED_STEP_REF
    assert pmn.assert_p7_r54_ahr_post_mn11_pmn_op19_actual_review_evidence_complete_predicate_contract(material) is True
    _assert_bodyfree_no_touch_no_promotion(
        material,
        allowed_true_false_flags=pmn.P7_R54_AHR_POST_MN11_PMN_OP19_ALLOWED_TRUE_FALSE_FLAG_REFS,
    )


@pytest.mark.parametrize(
    ("field", "bad_value"),
    [
        ("actual_review_evidence_complete", False),
        ("actual_review_evidence_complete_from_real_review", False),
        ("disposal_verified", False),
        ("downstream_manual_decision_hold_required", False),
        ("p5_final_allowed", True),
        ("p6_start_allowed", True),
        ("p8_start_allowed", True),
        ("actual_r52_reintake_execution_confirmed", True),
        ("release_allowed", True),
    ],
)
def test_pmn_op19_contract_rejects_predicate_or_downstream_promotion_mutation(field: str, bad_value: object) -> None:
    op11, op12, op13, op15, op16, _op17, op18 = _ready_chain()
    material = pmn.build_p7_r54_ahr_post_mn11_pmn_op19_actual_review_evidence_complete_predicate(
        final_no_body_no_question_no_path_no_hash_no_touch_validation=op18,
        actual_operation_receipt_intake=op11,
        sanitized_review_result_rows_intake=op12,
        rating_row_normalization_threshold_summary=op13,
        question_need_observation_row_normalization=op15,
        rating_question_consistency_guard=op16,
    )
    mutated = deepcopy(material)
    mutated[field] = bad_value

    with pytest.raises(ValueError):
        pmn.assert_p7_r54_ahr_post_mn11_pmn_op19_actual_review_evidence_complete_predicate_contract(mutated)


def test_pmn_op18_op19_aliases_match_primary_builders_and_contracts() -> None:
    op11, op12, op13, op15, op16, op17, primary_op18 = _ready_chain()
    alias_op18 = pmn.build_p7_r54_ahr_post_mn11_actual_operation_final_no_body_no_question_no_path_no_hash_no_touch_validation_bodyfree(
        disposal_purge_receipt_intake=op17,
        bodyfree_artifacts=[op11, op12, op13, op15, op16, op17],
    )
    assert alias_op18 == primary_op18
    assert pmn.assert_p7_r54_ahr_post_mn11_actual_operation_final_no_body_no_question_no_path_no_hash_no_touch_validation_bodyfree_contract(alias_op18) is True

    primary_op19 = pmn.build_p7_r54_ahr_post_mn11_pmn_op19_actual_review_evidence_complete_predicate(
        final_no_body_no_question_no_path_no_hash_no_touch_validation=primary_op18,
        actual_operation_receipt_intake=op11,
        sanitized_review_result_rows_intake=op12,
        rating_row_normalization_threshold_summary=op13,
        question_need_observation_row_normalization=op15,
        rating_question_consistency_guard=op16,
    )
    alias_op19 = pmn.build_p7_r54_ahr_post_mn11_actual_operation_actual_review_evidence_complete_predicate_bodyfree(
        final_no_body_no_question_no_path_no_hash_no_touch_validation=primary_op18,
        actual_operation_receipt_intake=op11,
        sanitized_review_result_rows_intake=op12,
        rating_row_normalization_threshold_summary=op13,
        question_need_observation_row_normalization=op15,
        rating_question_consistency_guard=op16,
    )
    assert alias_op19 == primary_op19
    assert pmn.assert_p7_r54_ahr_post_mn11_actual_operation_actual_review_evidence_complete_predicate_bodyfree_contract(alias_op19) is True
