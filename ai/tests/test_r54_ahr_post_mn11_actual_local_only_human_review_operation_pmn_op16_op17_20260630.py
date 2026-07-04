# -*- coding: utf-8 -*-
"""R54-AHR Post-MN11 actual local-only human review operation PMN-OP16/OP17 tests."""

from __future__ import annotations

from copy import deepcopy
from pathlib import Path
import sys

import pytest

TEST_DIR = Path(__file__).resolve().parent
if str(TEST_DIR) not in sys.path:
    sys.path.insert(0, str(TEST_DIR))

import emlis_ai_p7_r54_ahr_post_mn11_actual_local_only_human_review_operation_20260630 as pmn
import test_r54_ahr_post_mn11_actual_local_only_human_review_operation_pmn_op14_op15_20260630 as prev


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


def _ready_op12() -> dict[str, object]:
    return prev._ready_op12()


def _ready_op13(op12: dict[str, object] | None = None) -> dict[str, object]:
    source_op12 = op12 or _ready_op12()
    return prev._ready_op13(source_op12)


def _ready_op14(op12: dict[str, object] | None = None, op13: dict[str, object] | None = None) -> dict[str, object]:
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
    return pmn.build_p7_r54_ahr_post_mn11_pmn_op16_rating_question_consistency_guard(
        question_need_observation_row_normalization=source_op15,
        readfeel_label_connection_safe_display_blocker_classification=source_op14,
        rating_row_normalization_threshold_summary=source_op13,
    )


def _disposal_receipt(op16: dict[str, object]) -> dict[str, object]:
    return {
        "schema_version": "cocolon.emlis.p7_r54.ahr.post_mn11.disposal_receipt.bodyfree.v1",
        "disposal_receipt_ref": pmn.P7_R54_AHR_POST_MN11_PMN_OP17_DEFAULT_DISPOSAL_RECEIPT_REF,
        "review_session_id": op16["review_session_id"],
        "operation_receipt_ref": op16["operation_receipt_ref"],
        "disposal_status_ref": "BODY_PURGED",
        "packet_materialized_for_review": True,
        "body_removed": True,
        "reviewer_notes_removed": True,
        "temporary_form_removed": True,
        "content_hash_of_body_stored": False,
        "body_hash_stored": False,
        "local_absolute_path_included": False,
        "reviewer_notes_body_stored": False,
        "pause_abort_status_ref": "review_completed_without_abort_body_purged",
        "retention_policy_ref": pmn.P7_R54_AHR_POST_MN11_PMN_OP17_DEFAULT_RETENTION_POLICY_REF,
        "expiration_policy_ref": pmn.P7_R54_AHR_POST_MN11_PMN_OP17_DEFAULT_EXPIRATION_POLICY_REF,
        "actual_source_ref": pmn.P7_R54_AHR_POST_MN11_PMN_OP17_ALLOWED_ACTUAL_SOURCE_REF,
        "body_free": True,
    }


def _ready_op17(op16: dict[str, object] | None = None, receipt: dict[str, object] | None = None) -> dict[str, object]:
    source_op16 = op16 or _ready_op16()
    source_receipt = receipt or _disposal_receipt(source_op16)
    return pmn.build_p7_r54_ahr_post_mn11_pmn_op17_disposal_purge_receipt_intake(
        rating_question_consistency_guard=source_op16,
        disposal_receipt_bodyfree=source_receipt,
    )


def test_pmn_op00_to_op15_implementation_is_present_before_op16_op17() -> None:
    op15 = _ready_op15()

    assert pmn.assert_p7_r54_ahr_post_mn11_pmn_op15_question_need_observation_row_normalization_contract(op15) is True
    assert op15["question_need_observation_row_normalization_ready"] is True
    assert op15["question_need_observation_row_count"] == 24
    assert op15["next_required_step"] == pmn.P7_R54_AHR_POST_MN11_PMN_OP16_STEP_REF
    assert tuple(op15["implemented_steps"]) == pmn.P7_R54_AHR_POST_MN11_PMN_OP15_IMPLEMENTED_STEPS
    assert tuple(op15["not_yet_implemented_steps"]) == pmn.P7_R54_AHR_POST_MN11_PMN_OP15_NOT_YET_IMPLEMENTED_STEPS
    _assert_bodyfree_no_touch_no_promotion(op15)


def test_pmn_op16_blocks_until_op15_op14_op13_are_ready() -> None:
    material = pmn.build_p7_r54_ahr_post_mn11_pmn_op16_rating_question_consistency_guard()

    assert set(material) == set(pmn.P7_R54_AHR_POST_MN11_PMN_OP16_REQUIRED_FIELD_REFS)
    assert material["rating_question_consistency_guard_status_ref"] == pmn.P7_R54_AHR_POST_MN11_PMN_OP16_BLOCKED_STATUS_REF
    assert material["rating_question_consistency_guard_passed"] is False
    assert material["disposal_purge_receipt_intake_allowed_next"] is False
    assert material["consistency_issue_rows"] == []
    assert material["next_required_step"] == pmn.P7_R54_AHR_POST_MN11_PMN_OP16_BLOCKED_NEXT_REQUIRED_STEP_REF
    assert "pmn_op16_op15_question_need_observation_not_ready" in material["rating_question_consistency_guard_step_blocker_refs"]
    assert pmn.assert_p7_r54_ahr_post_mn11_pmn_op16_rating_question_consistency_guard_contract(material) is True
    _assert_bodyfree_no_touch_no_promotion(material)


def test_pmn_op16_passes_clean_rating_question_consistency_without_p8_escape() -> None:
    material = _ready_op16()

    assert set(material) == set(pmn.P7_R54_AHR_POST_MN11_PMN_OP16_REQUIRED_FIELD_REFS)
    assert material["schema_version"] == pmn.P7_R54_AHR_POST_MN11_PMN_OP16_RATING_QUESTION_CONSISTENCY_GUARD_SCHEMA_VERSION
    assert material["operation_step_ref"] == pmn.P7_R54_AHR_POST_MN11_PMN_OP16_STEP_REF
    assert material["rating_question_consistency_guard_status_ref"] == pmn.P7_R54_AHR_POST_MN11_PMN_OP16_READY_STATUS_REF
    assert material["rating_question_consistency_guard_passed"] is True
    assert material["rating_question_consistency_guard_step_blocker_refs"] == []
    assert material["consistency_issue_rows"] == []
    assert material["consistency_issue_row_count"] == 0
    assert material["op15_question_need_observation_row_count"] == 24
    assert material["op13_rating_row_count"] == 24
    assert material["rating_question_consistency_checked_here"] is True
    assert material["rating_question_consistency_guard_blocks_p8_escape"] is True
    assert material["weak_rating_or_blocker_not_treated_as_question_candidate"] is True
    assert material["safe_display_risk_not_question_candidate"] is True
    assert material["question_would_make_immediate_observation_heavy_not_p8_candidate"] is True
    assert material["disposal_purge_receipt_intake_allowed_next"] is True
    assert material["actual_review_evidence_complete_from_real_review_still_false"] is True
    assert tuple(material["implemented_steps"]) == pmn.P7_R54_AHR_POST_MN11_PMN_OP16_IMPLEMENTED_STEPS
    assert tuple(material["not_yet_implemented_steps"]) == pmn.P7_R54_AHR_POST_MN11_PMN_OP16_NOT_YET_IMPLEMENTED_STEPS
    assert material["next_required_step"] == pmn.P7_R54_AHR_POST_MN11_PMN_OP17_STEP_REF
    assert pmn.assert_p7_r54_ahr_post_mn11_pmn_op16_rating_question_consistency_guard_contract(material) is True
    _assert_bodyfree_no_touch_no_promotion(material)


def test_pmn_op16_detects_safe_display_candidate_resurface_without_creating_question_text() -> None:
    op11, rows = prev._rows_with_plus_candidate(safe_display_risk=True)
    op12 = prev._ready_op12_with_rows(rows, op11)
    op13 = _ready_op13(op12)
    op14 = _ready_op14(op12, op13)
    op15 = _ready_op15(op12, op14)
    mutated = deepcopy(op15)
    mutated["question_need_observation_rows"][0]["p8_material_candidate_only"] = True

    material = _ready_op16(op12=op12, op13=op13, op14=op14, op15=mutated)

    assert material["rating_question_consistency_guard_status_ref"] == pmn.P7_R54_AHR_POST_MN11_PMN_OP16_ISSUE_DETECTED_STATUS_REF
    assert material["rating_question_consistency_guard_passed"] is False
    assert material["consistency_issue_row_count"] >= 1
    assert material["safe_display_question_escape_issue_count"] == 1
    assert material["readfeel_blocker_question_escape_issue_count"] == 1
    assert material["repair_required_question_escape_issue_count"] == 1
    assert material["op14_blocked_candidate_resurfaced_issue_count"] == 1
    assert material["disposal_purge_receipt_intake_allowed_next"] is False
    for row in material["consistency_issue_rows"]:
        assert row["schema_version"] == pmn.P7_R54_AHR_POST_MN11_PMN_OP16_CONSISTENCY_ISSUE_ROW_SCHEMA_VERSION
        assert row["body_free"] is True
        assert row["p8_candidate_escape_detected"] is True
        assert row["p8_candidate_escape_blocked"] is True
        assert row["question_text_materialized_here"] is False
        assert row["draft_question_text_materialized_here"] is False
        assert row["p8_start_allowed"] is False
        for false_flag in pmn.P7_R54_AHR_POST_MN11_PMN_OP16_CONSISTENCY_ISSUE_ROW_FALSE_FLAG_REFS:
            assert row[false_flag] is False
    assert pmn.assert_p7_r54_ahr_post_mn11_pmn_op16_rating_question_consistency_guard_contract(material) is True
    _assert_bodyfree_no_touch_no_promotion(material)


def test_pmn_op16_detects_heavy_observation_p8_escape() -> None:
    op11, rows = prev._rows_with_plus_candidate(safe_display_risk=False)
    rows[0]["question_need_primary_class_ref"] = "question_would_make_immediate_observation_heavy"
    rows[0]["one_question_fit_ref"] = "would_delay_immediate_observation"
    op12 = prev._ready_op12_with_rows(rows, op11)
    op13 = _ready_op13(op12)
    op14 = _ready_op14(op12, op13)
    op15 = _ready_op15(op12, op14)
    mutated = deepcopy(op15)
    mutated["question_need_observation_rows"][0]["p8_material_candidate_only"] = True

    material = _ready_op16(op12=op12, op13=op13, op14=op14, op15=mutated)

    assert material["rating_question_consistency_guard_status_ref"] == pmn.P7_R54_AHR_POST_MN11_PMN_OP16_ISSUE_DETECTED_STATUS_REF
    assert material["heavy_observation_p8_escape_issue_count"] == 1
    assert any(row["issue_kind_ref"] == "heavy_observation_p8_escape" for row in material["consistency_issue_rows"])
    assert material["next_required_step"] == pmn.P7_R54_AHR_POST_MN11_PMN_OP16_BLOCKED_NEXT_REQUIRED_STEP_REF
    assert pmn.assert_p7_r54_ahr_post_mn11_pmn_op16_rating_question_consistency_guard_contract(material) is True
    _assert_bodyfree_no_touch_no_promotion(material)


@pytest.mark.parametrize(
    ("field", "bad_value"),
    [
        ("rating_question_consistency_guard_passed", False),
        ("rating_question_consistency_guard_blocks_p8_escape", False),
        ("weak_rating_or_blocker_not_treated_as_question_candidate", False),
        ("safe_display_risk_not_question_candidate", False),
        ("question_would_make_immediate_observation_heavy_not_p8_candidate", False),
        ("disposal_purge_receipt_intake_allowed_next", False),
        ("p8_start_allowed", True),
        ("actual_disposal_receipt_materialized_here", True),
        ("disposal_verified", True),
        ("actual_review_evidence_complete_from_real_review", True),
    ],
)
def test_pmn_op16_contract_rejects_consistency_or_promotion_mutation(field: str, bad_value: object) -> None:
    material = _ready_op16()
    mutated = deepcopy(material)
    mutated[field] = bad_value

    with pytest.raises(ValueError):
        pmn.assert_p7_r54_ahr_post_mn11_pmn_op16_rating_question_consistency_guard_contract(mutated)


def test_pmn_op17_blocks_until_disposal_receipt_is_supplied() -> None:
    op16 = _ready_op16()
    material = pmn.build_p7_r54_ahr_post_mn11_pmn_op17_disposal_purge_receipt_intake(
        rating_question_consistency_guard=op16
    )

    assert set(material) == set(pmn.P7_R54_AHR_POST_MN11_PMN_OP17_REQUIRED_FIELD_REFS)
    assert material["disposal_purge_receipt_intake_status_ref"] == pmn.P7_R54_AHR_POST_MN11_PMN_OP17_BLOCKED_STATUS_REF
    assert material["disposal_purge_receipt_intake_ready"] is False
    assert material["disposal_purge_receipt_accepted"] is False
    assert "pmn_op17_disposal_receipt_missing" in material["disposal_purge_receipt_blocker_refs"]
    assert material["body_full_packet_lifecycle_closed_bodyfree"] is False
    assert material["disposal_receipt_ready_for_final_no_leak_validation_only"] is False
    assert material["next_required_step"] == pmn.P7_R54_AHR_POST_MN11_PMN_OP17_BLOCKED_NEXT_REQUIRED_STEP_REF
    assert pmn.assert_p7_r54_ahr_post_mn11_pmn_op17_disposal_purge_receipt_intake_contract(material) is True
    _assert_bodyfree_no_touch_no_promotion(material)


def test_pmn_op17_accepts_bodyfree_disposal_receipt_without_claiming_verified_or_evidence_complete() -> None:
    op16 = _ready_op16()
    material = _ready_op17(op16=op16)

    assert set(material) == set(pmn.P7_R54_AHR_POST_MN11_PMN_OP17_REQUIRED_FIELD_REFS)
    assert material["schema_version"] == pmn.P7_R54_AHR_POST_MN11_PMN_OP17_DISPOSAL_PURGE_RECEIPT_INTAKE_SCHEMA_VERSION
    assert material["operation_step_ref"] == pmn.P7_R54_AHR_POST_MN11_PMN_OP17_STEP_REF
    assert material["disposal_purge_receipt_intake_status_ref"] == pmn.P7_R54_AHR_POST_MN11_PMN_OP17_READY_STATUS_REF
    assert material["disposal_purge_receipt_intake_ready"] is True
    assert material["disposal_purge_receipt_accepted"] is True
    assert material["disposal_receipt_ref_present"] is True
    assert material["disposal_receipt_ref_is_bodyfree_ref"] is True
    assert material["disposal_status_is_body_purged"] is True
    assert material["body_removed"] is True
    assert material["reviewer_notes_removed"] is True
    assert material["temporary_form_removed"] is True
    assert material["content_hash_of_body_stored"] is False
    assert material["body_hash_stored"] is False
    assert material["local_absolute_path_included"] is False
    assert material["reviewer_notes_body_stored"] is False
    assert material["actual_source_guard_passed"] is True
    assert material["body_full_packet_lifecycle_closed_bodyfree"] is True
    assert material["body_removed_without_hash_path_or_reviewer_notes"] is True
    assert material["disposal_receipt_ready_for_final_no_leak_validation_only"] is True
    assert material["actual_disposal_receipt_materialized_here"] is False
    assert material["disposal_verified"] is False
    assert material["actual_review_evidence_complete_from_real_review_still_false"] is True
    assert tuple(material["implemented_steps"]) == pmn.P7_R54_AHR_POST_MN11_PMN_OP17_IMPLEMENTED_STEPS
    assert tuple(material["not_yet_implemented_steps"]) == pmn.P7_R54_AHR_POST_MN11_PMN_OP17_NOT_YET_IMPLEMENTED_STEPS
    assert material["next_required_step"] == pmn.P7_R54_AHR_POST_MN11_PMN_OP18_STEP_REF
    assert pmn.assert_p7_r54_ahr_post_mn11_pmn_op17_disposal_purge_receipt_intake_contract(material) is True
    _assert_bodyfree_no_touch_no_promotion(material)


@pytest.mark.parametrize(
    ("receipt_field", "bad_value", "expected_blocker"),
    [
        ("disposal_status_ref", "DISPOSAL_FAILED", "pmn_op17_disposal_status_not_body_purged"),
        ("body_removed", False, "pmn_op17_body_removed_not_true"),
        ("reviewer_notes_removed", False, "pmn_op17_reviewer_notes_removed_not_true"),
        ("temporary_form_removed", False, "pmn_op17_temporary_form_removed_not_true"),
        ("actual_source_ref", "helper_default_rows", "pmn_op17_actual_source_ref_not_allowed"),
    ],
)
def test_pmn_op17_blocks_invalid_disposal_receipt_conditions(receipt_field: str, bad_value: object, expected_blocker: str) -> None:
    op16 = _ready_op16()
    receipt = _disposal_receipt(op16)
    receipt[receipt_field] = bad_value
    material = _ready_op17(op16=op16, receipt=receipt)

    assert material["disposal_purge_receipt_intake_ready"] is False
    assert expected_blocker in material["disposal_purge_receipt_blocker_refs"]
    assert material["next_required_step"] == pmn.P7_R54_AHR_POST_MN11_PMN_OP17_BLOCKED_NEXT_REQUIRED_STEP_REF
    assert pmn.assert_p7_r54_ahr_post_mn11_pmn_op17_disposal_purge_receipt_intake_contract(material) is True
    _assert_bodyfree_no_touch_no_promotion(material)


def test_pmn_op17_blocks_path_hash_or_reviewer_notes_leak() -> None:
    op16 = _ready_op16()
    receipt = _disposal_receipt(op16)
    receipt["body_hash_stored"] = True
    material = _ready_op17(op16=op16, receipt=receipt)

    assert material["disposal_purge_receipt_intake_status_ref"] == pmn.P7_R54_AHR_POST_MN11_PMN_OP17_BLOCKED_BY_LEAK_STATUS_REF
    assert material["disposal_purge_receipt_intake_ready"] is False
    assert "pmn_op17_body_hash_stored_not_false" in material["disposal_purge_receipt_blocker_refs"]
    assert material["body_hash_stored"] is True
    assert material["body_full_packet_lifecycle_closed_bodyfree"] is False
    assert material["actual_disposal_receipt_materialized_here"] is False
    assert material["disposal_verified"] is False
    assert pmn.assert_p7_r54_ahr_post_mn11_pmn_op17_disposal_purge_receipt_intake_contract(material) is True
    _assert_bodyfree_no_touch_no_promotion(material)


def test_pmn_op17_contract_rejects_ready_material_promotion_mutation() -> None:
    material = _ready_op17()
    mutated = deepcopy(material)
    mutated["disposal_verified"] = True

    with pytest.raises(ValueError):
        pmn.assert_p7_r54_ahr_post_mn11_pmn_op17_disposal_purge_receipt_intake_contract(mutated)


def test_pmn_op16_op17_aliases_match_primary_builders_and_contracts() -> None:
    op12 = _ready_op12()
    op13 = _ready_op13(op12)
    op14 = _ready_op14(op12, op13)
    op15 = _ready_op15(op12, op14)
    primary_op16 = pmn.build_p7_r54_ahr_post_mn11_pmn_op16_rating_question_consistency_guard(
        question_need_observation_row_normalization=op15,
        readfeel_label_connection_safe_display_blocker_classification=op14,
        rating_row_normalization_threshold_summary=op13,
    )
    alias_op16 = pmn.build_p7_r54_ahr_post_mn11_actual_operation_rating_question_consistency_guard_bodyfree(
        question_need_observation_row_normalization=op15,
        readfeel_label_connection_safe_display_blocker_classification=op14,
        rating_row_normalization_threshold_summary=op13,
    )
    assert alias_op16 == primary_op16
    assert pmn.assert_p7_r54_ahr_post_mn11_actual_operation_rating_question_consistency_guard_bodyfree_contract(alias_op16) is True

    receipt = _disposal_receipt(primary_op16)
    primary_op17 = pmn.build_p7_r54_ahr_post_mn11_pmn_op17_disposal_purge_receipt_intake(
        rating_question_consistency_guard=primary_op16,
        disposal_receipt_bodyfree=receipt,
    )
    alias_op17 = pmn.build_p7_r54_ahr_post_mn11_actual_operation_disposal_purge_receipt_intake_bodyfree(
        rating_question_consistency_guard=primary_op16,
        disposal_receipt_bodyfree=receipt,
    )
    assert alias_op17 == primary_op17
    assert pmn.assert_p7_r54_ahr_post_mn11_actual_operation_disposal_purge_receipt_intake_bodyfree_contract(alias_op17) is True
