# -*- coding: utf-8 -*-
"""R54-AHR Post-PMN23 downstream manual decision hold DMH-OP16/OP17 tests."""

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
import test_r54_ahr_post_pmn23_downstream_manual_decision_hold_evidence_intake_dmh_op10_op11_20260702 as dmh_op10_op11_prev
import test_r54_ahr_post_pmn23_downstream_manual_decision_hold_evidence_intake_dmh_op12_op13_20260702 as dmh_op12_op13_prev
import test_r54_ahr_post_pmn23_downstream_manual_decision_hold_evidence_intake_dmh_op14_op15_20260702 as dmh_op14_op15_prev

_READY_OP09_CACHE: dict[str, object] | None = None
_READY_OP10_CACHE: dict[str, object] | None = None
_READY_OP11_CACHE: dict[str, object] | None = None
_READY_OP12_CACHE: dict[str, object] | None = None
_READY_OP13_CACHE: dict[str, object] | None = None
_READY_OP14_CACHE: dict[str, object] | None = None
_READY_OP15_CACHE: dict[str, object] | None = None
_READY_OP16_CACHE: dict[str, object] | None = None
_READY_OP17_CACHE: dict[str, object] | None = None


def _ready_op09() -> dict[str, object]:
    global _READY_OP09_CACHE
    if _READY_OP09_CACHE is None:
        material = dmh_op08_op09_prev._ready_op09()
        assert dmh.assert_p7_r54_ahr_post_pmn23_dmh_op09_actual_operation_receipt_intake_contract(material) is True
        _READY_OP09_CACHE = material
    return deepcopy(_READY_OP09_CACHE)


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
        material = dmh_op12_op13_prev._ready_op12()
        assert dmh.assert_p7_r54_ahr_post_pmn23_dmh_op12_question_need_observation_rows_normalization_contract(material) is True
        _READY_OP12_CACHE = material
    return deepcopy(_READY_OP12_CACHE)


def _ready_op13() -> dict[str, object]:
    global _READY_OP13_CACHE
    if _READY_OP13_CACHE is None:
        material = dmh_op12_op13_prev._ready_op13()
        assert dmh.assert_p7_r54_ahr_post_pmn23_dmh_op13_rating_question_consistency_blocker_separation_contract(material) is True
        _READY_OP13_CACHE = material
    return deepcopy(_READY_OP13_CACHE)


def _ready_op14() -> dict[str, object]:
    global _READY_OP14_CACHE
    if _READY_OP14_CACHE is None:
        material = dmh_op14_op15_prev._ready_op14()
        assert dmh.assert_p7_r54_ahr_post_pmn23_dmh_op14_disposal_purge_receipt_intake_contract(material) is True
        _READY_OP14_CACHE = material
    return deepcopy(_READY_OP14_CACHE)


def _ready_op15() -> dict[str, object]:
    global _READY_OP15_CACHE
    if _READY_OP15_CACHE is None:
        material = dmh_op14_op15_prev._ready_op15()
        assert dmh.assert_p7_r54_ahr_post_pmn23_dmh_op15_final_no_body_no_question_no_path_no_hash_no_touch_validation_contract(material) is True
        _READY_OP15_CACHE = material
    return deepcopy(_READY_OP15_CACHE)


def _build_op16(**overrides: dict[str, object]) -> dict[str, object]:
    kwargs: dict[str, object] = {
        "final_no_body_no_question_no_path_no_hash_no_touch_validation": _ready_op15(),
        "actual_operation_receipt_intake": _ready_op09(),
        "sanitized_review_result_rows_intake": _ready_op10(),
        "rating_rows_normalization_threshold_summary": _ready_op11(),
        "question_need_observation_rows_normalization": _ready_op12(),
        "rating_question_consistency_blocker_separation": _ready_op13(),
        "disposal_purge_receipt_intake": _ready_op14(),
    }
    kwargs.update(overrides)
    return dmh.build_p7_r54_ahr_post_pmn23_dmh_op16_actual_review_evidence_complete_predicate(**kwargs)


def _ready_op16() -> dict[str, object]:
    global _READY_OP16_CACHE
    if _READY_OP16_CACHE is None:
        material = _build_op16()
        assert dmh.assert_p7_r54_ahr_post_pmn23_dmh_op16_actual_review_evidence_complete_predicate_contract(material) is True
        _READY_OP16_CACHE = material
    return deepcopy(_READY_OP16_CACHE)


def _ready_op17() -> dict[str, object]:
    global _READY_OP17_CACHE
    if _READY_OP17_CACHE is None:
        material = dmh.build_p7_r54_ahr_post_pmn23_dmh_op17_postcr22_ex07_ex18_actual_evidence_reentry_envelope(
            actual_review_evidence_complete_predicate=_ready_op16()
        )
        assert dmh.assert_p7_r54_ahr_post_pmn23_dmh_op17_postcr22_ex07_ex18_actual_evidence_reentry_envelope_contract(material) is True
        _READY_OP17_CACHE = material
    return deepcopy(_READY_OP17_CACHE)


def _assert_bodyfree_no_touch_no_downstream(material: dict[str, object], *, complete_allowed: bool) -> None:
    assert material["body_free"] is True
    for key in dmh.P7_R54_AHR_POST_PMN23_DMH_REQUIRED_FALSE_FLAG_REFS:
        expected = complete_allowed if key == "actual_review_evidence_complete_from_real_review" else False
        assert material[key] is expected, key
    for marker_map_key in ("public_contract", "post_pmn23_no_touch_contract", "body_free_markers"):
        assert material[marker_map_key]
        assert all(value is False for value in material[marker_map_key].values()), marker_map_key
    for forbidden_key in dmh.P7_R54_AHR_POST_PMN23_DMH_FORBIDDEN_PAYLOAD_KEY_REFS:
        assert forbidden_key not in material, forbidden_key
    assert material["p5_final_allowed"] is False
    assert material["p6_start_allowed"] is False
    assert material["p8_start_allowed"] is False
    assert material["p7_complete"] is False
    assert material["release_allowed"] is False
    assert material["r52_actual_execution_confirmed"] is False
    assert material["postcr22_ex07_ex18_reentry_executed_here"] is False


def test_dmh_op16_marks_actual_review_evidence_complete_predicate_only_after_all_bodyfree_evidence_boundaries_are_ready() -> None:
    material = _ready_op16()

    assert set(material) == set(dmh.P7_R54_AHR_POST_PMN23_DMH_OP16_REQUIRED_FIELD_REFS)
    assert material["schema_version"] == dmh.P7_R54_AHR_POST_PMN23_DMH_OP16_ACTUAL_REVIEW_EVIDENCE_COMPLETE_PREDICATE_SCHEMA_VERSION
    assert material["operation_step_ref"] == dmh.P7_R54_AHR_POST_PMN23_DMH_OP16_STEP_REF
    assert material["dmh_op16_status_ref"] == dmh.P7_R54_AHR_POST_PMN23_DMH_OP16_READY_STATUS_REF
    assert material["dmh_op16_ready"] is True
    assert tuple(material["dmh_op16_reason_refs"]) == dmh.P7_R54_AHR_POST_PMN23_DMH_OP16_READY_REASON_REFS
    assert tuple(material["complete_condition_refs"]) == dmh.P7_R54_AHR_POST_PMN23_DMH_OP16_COMPLETE_CONDITION_REFS
    assert tuple(material["complete_condition_passed_refs"]) == dmh.P7_R54_AHR_POST_PMN23_DMH_OP16_COMPLETE_CONDITION_REFS
    assert material["complete_condition_missing_refs"] == []
    assert material["actual_source_guard_passed"] is True
    assert material["actual_human_review_executed_by_person"] is True
    assert material["reviewed_case_count"] == dmh.P7_R54_AHR_POST_PMN23_DMH_REQUIRED_CASE_COUNT
    assert material["selection_row_count"] == dmh.P7_R54_AHR_POST_PMN23_DMH_REQUIRED_CASE_COUNT
    assert material["sanitized_review_result_row_count"] == dmh.P7_R54_AHR_POST_PMN23_DMH_REQUIRED_CASE_COUNT
    assert material["rating_row_count"] == dmh.P7_R54_AHR_POST_PMN23_DMH_REQUIRED_CASE_COUNT
    assert material["question_need_observation_row_count"] == dmh.P7_R54_AHR_POST_PMN23_DMH_REQUIRED_CASE_COUNT
    assert material["disposal_verified"] is True
    assert material["no_body_leak_validation_passed"] is True
    assert material["no_question_text_validation_passed"] is True
    assert material["no_path_hash_validation_passed"] is True
    assert material["no_touch_validation_passed"] is True
    assert material["consistency_guard_passed"] is True
    assert material["actual_review_evidence_complete_predicate_passed"] is True
    assert material["actual_review_evidence_complete_candidate_from_real_review"] is True
    assert material["actual_review_evidence_complete_from_real_review_before_op16"] is False
    assert material["actual_review_evidence_complete_from_real_review"] is True
    assert material["actual_review_evidence_complete_from_real_operation_claimed_here"] is False
    assert material["op16_does_not_run_actual_human_review_here"] is True
    assert material["op16_does_not_create_rows_here"] is True
    assert material["op16_does_not_run_disposal_here"] is True
    assert material["op16_does_not_execute_postcr22_ex_reentry"] is True
    assert material["op16_does_not_start_p5_p6_p8_r52_or_release"] is True
    assert tuple(material["implemented_steps"]) == dmh.P7_R54_AHR_POST_PMN23_DMH_OP16_IMPLEMENTED_STEPS
    assert tuple(material["not_yet_implemented_steps"]) == dmh.P7_R54_AHR_POST_PMN23_DMH_OP16_NOT_YET_IMPLEMENTED_STEPS
    assert material["next_required_step"] == dmh.P7_R54_AHR_POST_PMN23_DMH_OP17_STEP_REF
    _assert_bodyfree_no_touch_no_downstream(material, complete_allowed=True)


def test_dmh_op16_alias_builder_matches_direct_contract() -> None:
    material = dmh.build_p7_r54_ahr_post_pmn23_downstream_manual_decision_hold_actual_review_evidence_complete_predicate_bodyfree(
        final_no_body_no_question_no_path_no_hash_no_touch_validation=_ready_op15(),
        actual_operation_receipt_intake=_ready_op09(),
        sanitized_review_result_rows_intake=_ready_op10(),
        rating_rows_normalization_threshold_summary=_ready_op11(),
        question_need_observation_rows_normalization=_ready_op12(),
        rating_question_consistency_blocker_separation=_ready_op13(),
        disposal_purge_receipt_intake=_ready_op14(),
    )

    assert material["dmh_op16_ready"] is True
    assert dmh.assert_p7_r54_ahr_post_pmn23_downstream_manual_decision_hold_actual_review_evidence_complete_predicate_bodyfree_contract(material) is True


@pytest.mark.parametrize(
    ("argument_name", "expected_blocker"),
    [
        ("final_no_body_no_question_no_path_no_hash_no_touch_validation", "dmh_op16_op15_final_no_leak_validation_missing"),
        ("actual_operation_receipt_intake", "dmh_op16_op09_actual_operation_receipt_missing"),
        ("sanitized_review_result_rows_intake", "dmh_op16_op10_sanitized_rows_missing"),
        ("rating_rows_normalization_threshold_summary", "dmh_op16_op11_rating_rows_missing"),
        ("question_need_observation_rows_normalization", "dmh_op16_op12_question_need_observation_rows_missing"),
        ("rating_question_consistency_blocker_separation", "dmh_op16_op13_rating_question_consistency_missing"),
        ("disposal_purge_receipt_intake", "dmh_op16_op14_disposal_purge_receipt_intake_missing"),
    ],
)
def test_dmh_op16_blocks_when_required_prior_bodyfree_artifact_is_missing(argument_name: str, expected_blocker: str) -> None:
    material = _build_op16(**{argument_name: None})

    assert material["dmh_op16_ready"] is False
    assert material["dmh_op16_status_ref"] == dmh.P7_R54_AHR_POST_PMN23_DMH_OP16_BLOCKED_STATUS_REF
    assert expected_blocker in material["dmh_op16_blocker_refs"]
    assert material["actual_review_evidence_complete_from_real_review"] is False
    assert material["next_required_step"] == dmh.P7_R54_AHR_POST_PMN23_DMH_OP16_BLOCKED_NEXT_REQUIRED_STEP_REF
    assert dmh.assert_p7_r54_ahr_post_pmn23_dmh_op16_actual_review_evidence_complete_predicate_contract(material) is True
    _assert_bodyfree_no_touch_no_downstream(material, complete_allowed=False)


@pytest.mark.parametrize(
    ("mutator", "expected_blocker"),
    [
        (lambda artifacts: artifacts["op15"].__setitem__("final_no_leak_validation_passed", False), "dmh_op16_op15_final_no_leak_validation_invalid"),
        (lambda artifacts: artifacts["op15"].__setitem__("next_required_step", dmh.P7_R54_AHR_POST_PMN23_DMH_OP15_BLOCKED_NEXT_REQUIRED_STEP_REF), "dmh_op16_op15_final_no_leak_validation_invalid"),
        (lambda artifacts: artifacts["op09"].__setitem__("actual_source_guard_passed", False), "dmh_op16_op09_actual_operation_receipt_invalid"),
        (lambda artifacts: artifacts["op09"].__setitem__("actual_human_review_executed_by_person", False), "dmh_op16_op09_actual_operation_receipt_invalid"),
        (lambda artifacts: artifacts["op09"].__setitem__("reviewed_case_count", 23), "dmh_op16_op09_actual_operation_receipt_invalid"),
        (lambda artifacts: artifacts["op09"].__setitem__("selection_row_count", 23), "dmh_op16_op09_actual_operation_receipt_invalid"),
        (lambda artifacts: artifacts["op10"].__setitem__("row_provenance_guard_passed", False), "dmh_op16_op10_sanitized_rows_invalid"),
        (lambda artifacts: artifacts["op10"].__setitem__("sanitized_review_result_row_count", 23), "dmh_op16_op10_sanitized_rows_invalid"),
        (lambda artifacts: artifacts["op11"].__setitem__("rating_row_count", 23), "dmh_op16_op11_rating_rows_invalid"),
        (lambda artifacts: artifacts["op12"].__setitem__("question_need_observation_row_count", 23), "dmh_op16_op12_question_need_observation_rows_invalid"),
        (lambda artifacts: artifacts["op13"].__setitem__("rating_question_consistency_guard_passed", False), "dmh_op16_op13_rating_question_consistency_invalid"),
        (lambda artifacts: artifacts["op14"].__setitem__("disposal_purge_receipt_accepted", False), "dmh_op16_op14_disposal_purge_receipt_intake_invalid"),
    ],
)
def test_dmh_op16_blocks_when_prior_artifact_contract_or_complete_condition_is_mutated(mutator, expected_blocker: str) -> None:
    artifacts = {
        "op15": _ready_op15(),
        "op09": _ready_op09(),
        "op10": _ready_op10(),
        "op11": _ready_op11(),
        "op12": _ready_op12(),
        "op13": _ready_op13(),
        "op14": _ready_op14(),
    }
    mutator(artifacts)
    material = _build_op16(
        final_no_body_no_question_no_path_no_hash_no_touch_validation=artifacts["op15"],
        actual_operation_receipt_intake=artifacts["op09"],
        sanitized_review_result_rows_intake=artifacts["op10"],
        rating_rows_normalization_threshold_summary=artifacts["op11"],
        question_need_observation_rows_normalization=artifacts["op12"],
        rating_question_consistency_blocker_separation=artifacts["op13"],
        disposal_purge_receipt_intake=artifacts["op14"],
    )

    assert material["dmh_op16_ready"] is False
    assert expected_blocker in material["dmh_op16_blocker_refs"]
    assert material["actual_review_evidence_complete_predicate_passed"] is False
    assert material["actual_review_evidence_complete_from_real_review"] is False
    assert dmh.assert_p7_r54_ahr_post_pmn23_dmh_op16_actual_review_evidence_complete_predicate_contract(material) is True


def test_dmh_op16_blocks_session_mismatch_across_evidence_bundle() -> None:
    op10 = _ready_op10()
    op10["review_session_id"] = "other_bodyfree_session"
    material = _build_op16(sanitized_review_result_rows_intake=op10)

    assert material["dmh_op16_ready"] is False
    assert "dmh_op16_review_session_id_mismatch_across_evidence_bundle" in material["dmh_op16_blocker_refs"]
    assert material["actual_review_evidence_complete_from_real_review"] is False
    assert dmh.assert_p7_r54_ahr_post_pmn23_dmh_op16_actual_review_evidence_complete_predicate_contract(material) is True


def test_dmh_op16_blocks_operation_receipt_ref_mismatch_across_evidence_bundle() -> None:
    op13 = _ready_op13()
    op13["operation_receipt_ref"] = "other_operation_receipt_ref_bodyfree"
    material = _build_op16(rating_question_consistency_blocker_separation=op13)

    assert material["dmh_op16_ready"] is False
    assert "dmh_op16_operation_receipt_ref_mismatch_across_evidence_bundle" in material["dmh_op16_blocker_refs"]
    assert material["actual_review_evidence_complete_from_real_review"] is False
    assert dmh.assert_p7_r54_ahr_post_pmn23_dmh_op16_actual_review_evidence_complete_predicate_contract(material) is True


def test_dmh_op16_blocks_forbidden_payload_key_in_prior_bodyfree_artifact() -> None:
    op11 = _ready_op11()
    op11["raw_input"] = "must never pass"
    material = _build_op16(rating_rows_normalization_threshold_summary=op11)

    assert material["dmh_op16_ready"] is False
    assert "dmh_op16_op11_forbidden_payload_key_detected" in material["dmh_op16_blocker_refs"]
    assert material["actual_review_evidence_complete_from_real_review"] is False
    assert dmh.assert_p7_r54_ahr_post_pmn23_dmh_op16_actual_review_evidence_complete_predicate_contract(material) is True


@pytest.mark.parametrize(
    ("field", "bad_value"),
    [
        ("dmh_op16_ready", False),
        ("dmh_op16_status_ref", dmh.P7_R54_AHR_POST_PMN23_DMH_OP16_BLOCKED_STATUS_REF),
        ("actual_source_guard_passed", False),
        ("actual_human_review_executed_by_person", False),
        ("reviewed_case_count", 23),
        ("sanitized_review_result_row_count", 23),
        ("rating_row_count", 23),
        ("question_need_observation_row_count", 23),
        ("disposal_verified", False),
        ("no_body_leak_validation_passed", False),
        ("no_question_text_validation_passed", False),
        ("no_path_hash_validation_passed", False),
        ("no_touch_validation_passed", False),
        ("consistency_guard_passed", False),
        ("actual_review_evidence_complete_predicate_passed", False),
        ("actual_review_evidence_complete_from_real_review", False),
        ("postcr22_ex07_ex18_reentry_executed_here", True),
        ("p5_final_allowed", True),
        ("p6_start_allowed", True),
        ("p8_start_allowed", True),
        ("r52_actual_execution_confirmed", True),
        ("p7_complete", True),
        ("release_allowed", True),
        ("next_required_step", dmh.P7_R54_AHR_POST_PMN23_DMH_OP16_BLOCKED_NEXT_REQUIRED_STEP_REF),
    ],
)
def test_dmh_op16_contract_rejects_ready_material_mutations(field: str, bad_value: object) -> None:
    material = _ready_op16()
    material[field] = bad_value

    with pytest.raises(ValueError):
        dmh.assert_p7_r54_ahr_post_pmn23_dmh_op16_actual_review_evidence_complete_predicate_contract(material)


def test_dmh_op16_contract_rejects_condition_count_tampering() -> None:
    material = _ready_op16()
    material["complete_condition_passed_ref_count"] = 1

    with pytest.raises(ValueError):
        dmh.assert_p7_r54_ahr_post_pmn23_dmh_op16_actual_review_evidence_complete_predicate_contract(material)


def test_dmh_op17_builds_bodyfree_postcr22_ex07_ex18_reentry_envelope_without_executing_reentry_or_r52() -> None:
    material = _ready_op17()

    assert set(material) == set(dmh.P7_R54_AHR_POST_PMN23_DMH_OP17_REQUIRED_FIELD_REFS)
    assert material["schema_version"] == dmh.P7_R54_AHR_POST_PMN23_DMH_OP17_POSTCR22_EX07_EX18_ACTUAL_EVIDENCE_REENTRY_ENVELOPE_SCHEMA_VERSION
    assert material["operation_step_ref"] == dmh.P7_R54_AHR_POST_PMN23_DMH_OP17_STEP_REF
    assert material["dmh_op17_status_ref"] == dmh.P7_R54_AHR_POST_PMN23_DMH_OP17_READY_STATUS_REF
    assert material["dmh_op17_ready"] is True
    assert tuple(material["dmh_op17_reason_refs"]) == dmh.P7_R54_AHR_POST_PMN23_DMH_OP17_READY_REASON_REFS
    assert material["op16_dmh_ready"] is True
    assert material["op16_actual_review_evidence_complete_predicate_passed"] is True
    assert material["op16_actual_review_evidence_complete_from_real_review"] is True
    assert material["postcr22_ex07_ex18_reentry_envelope_ready"] is True
    assert material["postcr22_ex07_ex18_reentry_executed_here"] is False
    assert material["postcr22_ex07_ex18_reentry_execution_requested_here"] is False
    assert material["r52_actual_execution_started_here"] is False
    assert material["r52_actual_execution_confirmed"] is False
    assert material["candidate_only_separation_preserved"] is True
    assert material["actual_review_evidence_complete_from_real_review"] is True
    assert material["actual_review_evidence_complete_predicate_carried_into_reentry_envelope"] is True
    assert material["postcr22_ex07_ex18_mapping_row_count"] == len(dmh.P7_R54_AHR_POST_PMN23_DMH_OP17_REENTRY_MAPPING_REFS)
    assert tuple((row["source_ref"], row["target_ref"]) for row in material["postcr22_ex07_ex18_mapping_rows"]) == dmh.P7_R54_AHR_POST_PMN23_DMH_OP17_REENTRY_MAPPING_REFS
    assert all(row["body_free"] is True for row in material["postcr22_ex07_ex18_mapping_rows"])
    assert all(row["reentry_executed_here"] is False for row in material["postcr22_ex07_ex18_mapping_rows"])
    assert all(row["r52_actual_execution_started_here"] is False for row in material["postcr22_ex07_ex18_mapping_rows"])
    assert tuple(material["implemented_steps"]) == dmh.P7_R54_AHR_POST_PMN23_DMH_OP17_IMPLEMENTED_STEPS
    assert tuple(material["not_yet_implemented_steps"]) == dmh.P7_R54_AHR_POST_PMN23_DMH_OP17_NOT_YET_IMPLEMENTED_STEPS
    assert material["next_required_step"] == dmh.P7_R54_AHR_POST_PMN23_DMH_OP18_STEP_REF
    _assert_bodyfree_no_touch_no_downstream(material, complete_allowed=True)


def test_dmh_op17_alias_builder_matches_direct_contract() -> None:
    material = dmh.build_p7_r54_ahr_post_pmn23_downstream_manual_decision_hold_postcr22_ex07_ex18_actual_evidence_reentry_envelope_bodyfree(
        actual_review_evidence_complete_predicate=_ready_op16()
    )

    assert material["dmh_op17_ready"] is True
    assert dmh.assert_p7_r54_ahr_post_pmn23_downstream_manual_decision_hold_postcr22_ex07_ex18_actual_evidence_reentry_envelope_bodyfree_contract(material) is True


def test_dmh_op17_blocks_without_op16_predicate() -> None:
    material = dmh.build_p7_r54_ahr_post_pmn23_dmh_op17_postcr22_ex07_ex18_actual_evidence_reentry_envelope()

    assert material["dmh_op17_ready"] is False
    assert material["dmh_op17_status_ref"] == dmh.P7_R54_AHR_POST_PMN23_DMH_OP17_BLOCKED_STATUS_REF
    assert "dmh_op17_op16_actual_review_evidence_complete_predicate_missing" in material["dmh_op17_blocker_refs"]
    assert material["postcr22_ex07_ex18_reentry_envelope_ready"] is False
    assert material["actual_review_evidence_complete_from_real_review"] is False
    assert material["postcr22_ex07_ex18_mapping_rows"] == []
    assert material["next_required_step"] == dmh.P7_R54_AHR_POST_PMN23_DMH_OP17_BLOCKED_NEXT_REQUIRED_STEP_REF
    assert dmh.assert_p7_r54_ahr_post_pmn23_dmh_op17_postcr22_ex07_ex18_actual_evidence_reentry_envelope_contract(material) is True
    _assert_bodyfree_no_touch_no_downstream(material, complete_allowed=False)


@pytest.mark.parametrize(
    ("field", "bad_value", "expected_blocker"),
    [
        ("dmh_op16_ready", False, "dmh_op17_op16_actual_review_evidence_complete_predicate_invalid"),
        ("actual_review_evidence_complete_predicate_passed", False, "dmh_op17_op16_actual_review_evidence_complete_predicate_invalid"),
        ("actual_review_evidence_complete_from_real_review", False, "dmh_op17_op16_actual_review_evidence_complete_predicate_invalid"),
        ("next_required_step", dmh.P7_R54_AHR_POST_PMN23_DMH_OP16_BLOCKED_NEXT_REQUIRED_STEP_REF, "dmh_op17_op16_actual_review_evidence_complete_predicate_invalid"),
    ],
)
def test_dmh_op17_blocks_if_op16_predicate_was_mutated(field: str, bad_value: object, expected_blocker: str) -> None:
    op16 = _ready_op16()
    op16[field] = bad_value
    material = dmh.build_p7_r54_ahr_post_pmn23_dmh_op17_postcr22_ex07_ex18_actual_evidence_reentry_envelope(
        actual_review_evidence_complete_predicate=op16
    )

    assert material["dmh_op17_ready"] is False
    assert expected_blocker in material["dmh_op17_blocker_refs"]
    assert material["postcr22_ex07_ex18_reentry_envelope_ready"] is False
    assert material["postcr22_ex07_ex18_reentry_executed_here"] is False
    assert material["r52_actual_execution_started_here"] is False
    assert material["actual_review_evidence_complete_from_real_review"] is False
    assert dmh.assert_p7_r54_ahr_post_pmn23_dmh_op17_postcr22_ex07_ex18_actual_evidence_reentry_envelope_contract(material) is True


def test_dmh_op17_blocks_forbidden_payload_key_in_op16_predicate() -> None:
    op16 = _ready_op16()
    op16["raw_input"] = "must never pass"
    material = dmh.build_p7_r54_ahr_post_pmn23_dmh_op17_postcr22_ex07_ex18_actual_evidence_reentry_envelope(
        actual_review_evidence_complete_predicate=op16
    )

    assert material["dmh_op17_ready"] is False
    assert "dmh_op17_op16_actual_review_evidence_complete_predicate_invalid" in material["dmh_op17_blocker_refs"]
    assert "dmh_op17_op16_forbidden_payload_key_detected" in material["dmh_op17_blocker_refs"]
    assert material["actual_review_evidence_complete_from_real_review"] is False
    assert dmh.assert_p7_r54_ahr_post_pmn23_dmh_op17_postcr22_ex07_ex18_actual_evidence_reentry_envelope_contract(material) is True


@pytest.mark.parametrize(
    ("field", "bad_value"),
    [
        ("dmh_op17_ready", False),
        ("dmh_op17_status_ref", dmh.P7_R54_AHR_POST_PMN23_DMH_OP17_BLOCKED_STATUS_REF),
        ("op16_dmh_ready", False),
        ("op16_actual_review_evidence_complete_predicate_passed", False),
        ("op16_actual_review_evidence_complete_from_real_review", False),
        ("postcr22_ex07_ex18_reentry_envelope_ready", False),
        ("postcr22_ex07_ex18_reentry_executed_here", True),
        ("postcr22_ex07_ex18_reentry_execution_requested_here", True),
        ("r52_actual_execution_started_here", True),
        ("r52_actual_execution_confirmed", True),
        ("candidate_only_separation_preserved", False),
        ("actual_review_evidence_complete_from_real_review", False),
        ("actual_review_evidence_complete_predicate_carried_into_reentry_envelope", False),
        ("p5_final_allowed", True),
        ("p6_start_allowed", True),
        ("p8_start_allowed", True),
        ("p7_complete", True),
        ("release_allowed", True),
        ("next_required_step", dmh.P7_R54_AHR_POST_PMN23_DMH_OP17_BLOCKED_NEXT_REQUIRED_STEP_REF),
    ],
)
def test_dmh_op17_contract_rejects_ready_material_mutations(field: str, bad_value: object) -> None:
    material = _ready_op17()
    material[field] = bad_value

    with pytest.raises(ValueError):
        dmh.assert_p7_r54_ahr_post_pmn23_dmh_op17_postcr22_ex07_ex18_actual_evidence_reentry_envelope_contract(material)


def test_dmh_op17_contract_rejects_mapping_row_execution_or_r52_promotion() -> None:
    material = _ready_op17()
    material["postcr22_ex07_ex18_mapping_rows"][0]["reentry_executed_here"] = True

    with pytest.raises(ValueError):
        dmh.assert_p7_r54_ahr_post_pmn23_dmh_op17_postcr22_ex07_ex18_actual_evidence_reentry_envelope_contract(material)


def test_dmh_op17_contract_rejects_mapping_count_tampering() -> None:
    material = _ready_op17()
    material["postcr22_ex07_ex18_mapping_row_count"] = 1

    with pytest.raises(ValueError):
        dmh.assert_p7_r54_ahr_post_pmn23_dmh_op17_postcr22_ex07_ex18_actual_evidence_reentry_envelope_contract(material)


def test_dmh_op16_op17_keep_p5_p6_p8_r52_p7_release_closed_even_when_predicate_and_envelope_are_ready() -> None:
    op16 = _ready_op16()
    op17 = _ready_op17()

    for material in (op16, op17):
        assert material["actual_review_evidence_complete_from_real_review"] is True
        assert material["p5_final_allowed"] is False
        assert material["p6_start_allowed"] is False
        assert material["p8_start_allowed"] is False
        assert material["r52_actual_execution_confirmed"] is False
        assert material["p7_complete"] is False
        assert material["release_allowed"] is False
        assert material["postcr22_ex07_ex18_reentry_executed_here"] is False
        _assert_bodyfree_no_touch_no_downstream(material, complete_allowed=True)
