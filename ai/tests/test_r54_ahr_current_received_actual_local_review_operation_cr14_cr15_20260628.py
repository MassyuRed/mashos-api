# -*- coding: utf-8 -*-
"""R54-AHR-CR14/CR15 current received actual local review operation tests."""

from __future__ import annotations

from copy import deepcopy

import pytest

import emlis_ai_p7_r54_ahr_current_received_snapshot_actual_local_review_operation_20260628 as cr


def _assert_bodyfree_no_touch(material: dict[str, object], *, allowed_true_flags: tuple[str, ...] = ()) -> None:
    assert material["body_free"] is True
    allowed = set(allowed_true_flags)
    for key in cr.P7_R54_AHR_CR_FALSE_FLAG_REFS:
        if key in allowed:
            assert material[key] in (False, True), key
            continue
        assert material[key] is False, key
    for flag_map_key in ("public_contract", "r54_ahr_cr_no_touch_contract", "body_free_markers"):
        assert material[flag_map_key]
        assert all(value is False for value in material[flag_map_key].values()), flag_map_key
    for forbidden_key in (
        "raw_input",
        "raw_body",
        "current_input_body",
        "returned_emlis_body",
        "history_surface",
        "comment_text",
        "reviewer_free_text",
        "reviewer_notes_body",
        "question_text",
        "draft_question_text",
        "packet_content",
        "body_full_packet_content",
        "local_path",
        "local_absolute_path",
        "body_hash",
        "terminal_output_body",
    ):
        assert forbidden_key not in material


def _cr05_ready() -> dict[str, object]:
    return cr.build_p7_r54_ahr_cr05_local_only_preflight(
        explicit_allow_ref=cr.P7_R54_AHR_CR05_DEFAULT_EXPLICIT_ALLOW_REF,
    )


def _cr06_ready() -> dict[str, object]:
    return cr.build_p7_r54_ahr_cr06_packet_generation_request_bridge(local_only_preflight=_cr05_ready())


def _cr07_ready() -> dict[str, object]:
    return cr.build_p7_r54_ahr_cr07_packet_generation_receipt_and_scan(
        packet_generation_request_bridge=_cr06_ready(),
        receipt_input=cr.build_p7_r54_ahr_cr07_bodyfree_receipt_input(),
    )


def _cr08_ready() -> dict[str, object]:
    return cr.build_p7_r54_ahr_cr08_reviewer_selection_form(
        packet_generation_receipt_scan=_cr07_ready(),
        reviewer_person_ref=cr.P7_R54_AHR_CR08_DEFAULT_REVIEWER_PERSON_REF,
        reviewer_is_person=True,
        reviewer_person_confirmed=True,
    )


def _cr09_ready() -> dict[str, object]:
    return cr.build_p7_r54_ahr_cr09_actual_local_human_review_operation_receipt(
        reviewer_selection_form=_cr08_ready(),
        operation_receipt_input=cr.build_p7_r54_ahr_cr09_bodyfree_operation_receipt_input(),
    )


def _selection_rows() -> list[dict[str, object]]:
    return cr.build_p7_r54_ahr_cr10_bodyfree_selection_result_rows_input()


def _cr10_ready(rows: list[dict[str, object]] | None = None) -> dict[str, object]:
    return cr.build_p7_r54_ahr_cr10_sanitized_selection_only_result_rows_intake(
        actual_local_human_review_operation_receipt=_cr09_ready(),
        selection_result_rows=rows or _selection_rows(),
    )


def _cr11_ready(cr10_material: dict[str, object] | None = None) -> dict[str, object]:
    return cr.build_p7_r54_ahr_cr11_rating_row_normalization(
        sanitized_selection_only_result_rows_intake=cr10_material or _cr10_ready(),
    )


def _cr12_ready(cr11_material: dict[str, object] | None = None) -> dict[str, object]:
    return cr.build_p7_r54_ahr_cr12_readfeel_execution_blocker_normalization(
        rating_row_normalization=cr11_material or _cr11_ready(),
    )


def _cr13_ready(
    cr10_material: dict[str, object] | None = None,
    cr11_material: dict[str, object] | None = None,
    cr12_material: dict[str, object] | None = None,
) -> dict[str, object]:
    cr10 = cr10_material or _cr10_ready()
    cr11 = cr11_material or _cr11_ready(cr10)
    cr12 = cr12_material or _cr12_ready(cr11)
    return cr.build_p7_r54_ahr_cr13_question_need_observation_normalization(
        sanitized_selection_only_result_rows_intake=cr10,
        rating_row_normalization=cr11,
        readfeel_execution_blocker_normalization=cr12,
    )


def _cr14_ready(
    cr11_material: dict[str, object] | None = None,
    cr12_material: dict[str, object] | None = None,
    cr13_material: dict[str, object] | None = None,
) -> dict[str, object]:
    cr11 = cr11_material or _cr11_ready()
    cr12 = cr12_material or _cr12_ready(cr11)
    cr13 = cr13_material or _cr13_ready(cr11_material=cr11, cr12_material=cr12)
    return cr.build_p7_r54_ahr_cr14_rating_question_consistency_guard(
        rating_row_normalization=cr11,
        readfeel_execution_blocker_normalization=cr12,
        question_need_observation_normalization=cr13,
    )


def _cr15_ready(cr14_material: dict[str, object] | None = None, receipt: dict[str, object] | None = None) -> dict[str, object]:
    return cr.build_p7_r54_ahr_cr15_pause_abort_expiration_disposal_receipt(
        rating_question_consistency_guard=cr14_material or _cr14_ready(),
        disposal_receipt_input=receipt or cr.build_p7_r54_ahr_cr15_bodyfree_disposal_receipt_input(),
    )


def _mutated_cr13_rating_below_target_p8_escape() -> tuple[dict[str, object], dict[str, object], dict[str, object]]:
    rows = _selection_rows()
    rows[0]["axis_scores"] = {axis: 1.0 for axis in cr.P7_R54_AHR_CR08_RATING_AXIS_REFS}
    rows[0]["axis_scores"]["history_connection_naturalness"] = 0.10
    rows[0]["question_need_primary_class"] = "question_may_reduce_overread_risk"
    rows[0]["one_question_fit_ref"] = "fits_one_question"
    rows[0]["plan_candidate_flags"]["p8_design_material_candidate"] = True
    cr10 = _cr10_ready(rows)
    cr11 = _cr11_ready(cr10)
    cr12 = _cr12_ready(cr11)
    cr13 = _cr13_ready(cr10, cr11, cr12)
    first = cr13["question_need_observation_rows"][0]
    first["p8_design_material_candidate"] = True
    first["p8_material_candidate_reason_ref"] = "p8_material_candidate_bodyfree_only"
    first["p5_repair_required"] = False
    first["readfeel_blocker_present"] = False
    cr13["p8_material_candidate_case_refs"] = [first["case_ref_id"]]
    cr13["p8_material_candidate_case_count"] = 1
    return cr11, cr12, cr13


def test_cr14_blocks_by_default_without_ready_cr11_cr12_cr13_chain() -> None:
    material = cr.build_p7_r54_ahr_cr14_rating_question_consistency_guard()

    assert set(material) == set(cr.P7_R54_AHR_CR14_RATING_QUESTION_CONSISTENCY_GUARD_REQUIRED_FIELD_REFS)
    assert material["schema_version"] == cr.P7_R54_AHR_CR_RATING_QUESTION_CONSISTENCY_GUARD_SCHEMA_VERSION
    assert material["operation_step_ref"] == cr.P7_R54_AHR_CR14_STEP_REF
    assert material["rating_question_consistency_guard_status_ref"] == cr.P7_R54_AHR_CR14_GUARD_BLOCKED_STATUS_REF
    assert material["rating_question_consistency_guard_evaluated"] is False
    assert material["rating_question_consistency_guard_passed"] is False
    assert cr.P7_R54_AHR_CR14_CR11_NOT_READY_BLOCKER_REF in material["rating_question_consistency_guard_step_blocker_refs"]
    assert material["consistency_issue_rows"] == []
    assert material["actual_review_evidence_complete"] is False
    assert material["actual_disposal_receipt_materialized_here"] is False
    assert material["next_required_step"] == cr.P7_R54_AHR_CR14_DEFAULT_BLOCKED_NEXT_REQUIRED_STEP_REF
    _assert_bodyfree_no_touch(material, allowed_true_flags=cr.P7_R54_AHR_CR14_ALLOWED_TRUE_OPERATION_FLAG_REFS)
    assert cr.assert_p7_r54_ahr_cr14_rating_question_consistency_guard_contract(material) is True


def test_cr14_passes_clean_rating_question_consistency_without_disposal_or_evidence_completion() -> None:
    material = _cr14_ready()

    assert set(material) == set(cr.P7_R54_AHR_CR14_RATING_QUESTION_CONSISTENCY_GUARD_REQUIRED_FIELD_REFS)
    assert material["rating_question_consistency_guard_status_ref"] == cr.P7_R54_AHR_CR14_GUARD_PASSED_STATUS_REF
    assert material["rating_question_consistency_guard_evaluated"] is True
    assert material["rating_question_consistency_guard_passed"] is True
    assert material["rating_question_consistency_guard_reason_refs"] == [cr.P7_R54_AHR_CR14_READY_REASON_REF]
    assert material["consistency_issue_row_count"] == 0
    assert material["source_rating_row_count"] == 24
    assert material["source_question_need_observation_row_count"] == 24
    assert material["case_ref_ids_unique"] is True
    assert material["rating_question_consistency_guarded_here"] is True
    assert material["rating_below_target_cannot_escape_to_p8_material"] is True
    assert material["repair_or_blocker_rows_cannot_escape_to_p8_material"] is True
    assert material["actual_rating_rows_materialized_here"] is True
    assert material["actual_question_need_observation_rows_materialized_here"] is True
    assert material["actual_human_review_executed_by_person"] is True
    assert material["actual_review_evidence_complete"] is False
    assert material["actual_disposal_receipt_materialized_here"] is False
    assert material["p8_start_allowed"] is False
    assert material["release_allowed"] is False
    assert tuple(material["implemented_steps"]) == cr.P7_R54_AHR_CR14_IMPLEMENTED_STEPS
    assert tuple(material["not_yet_implemented_steps"]) == cr.P7_R54_AHR_CR14_NOT_YET_IMPLEMENTED_STEPS
    assert material["next_required_step"] == cr.P7_R54_AHR_CR15_STEP_REF
    _assert_bodyfree_no_touch(material, allowed_true_flags=cr.P7_R54_AHR_CR14_ALLOWED_TRUE_OPERATION_FLAG_REFS)
    assert cr.assert_p7_r54_ahr_cr14_rating_question_consistency_guard_contract(material) is True


def test_cr14_detects_rating_below_target_p8_candidate_escape_and_blocks_next_step() -> None:
    cr11, cr12, cr13 = _mutated_cr13_rating_below_target_p8_escape()
    material = _cr14_ready(cr11, cr12, cr13)

    assert material["rating_question_consistency_guard_status_ref"] == cr.P7_R54_AHR_CR14_GUARD_FAILED_STATUS_REF
    assert material["rating_question_consistency_guard_evaluated"] is True
    assert material["rating_question_consistency_guard_passed"] is False
    assert material["consistency_issue_row_count"] >= 1
    assert cr.P7_R54_AHR_CR14_ISSUE_RATING_BELOW_TARGET_P8_ESCAPE_REF in material["consistency_issue_type_counts"]
    assert material["rating_below_target_p8_escape_case_count"] == 1
    assert material["actual_review_evidence_complete"] is False
    assert material["p8_start_allowed"] is False
    assert material["next_required_step"] == cr.P7_R54_AHR_CR14_DEFAULT_BLOCKED_NEXT_REQUIRED_STEP_REF
    for row in material["consistency_issue_rows"]:
        assert set(row) == set(cr.P7_R54_AHR_CR14_CONSISTENCY_ISSUE_ROW_REQUIRED_FIELD_REFS)
        assert row["schema_version"] == cr.P7_R54_AHR_CR14_CONSISTENCY_ISSUE_ROW_SCHEMA_VERSION
        assert row["rating_question_consistency_guard_blocks_evidence_complete"] is True
        assert row["p8_material_candidate_blocked"] is True
        assert row["body_free"] is True
    assert cr.assert_p7_r54_ahr_cr14_rating_question_consistency_guard_contract(material) is True


@pytest.mark.parametrize(
    "axis,expected_issue",
    [
        ("creepy_absence", cr.P7_R54_AHR_CR14_ISSUE_CREEPY_OVERCLAIM_P8_ESCAPE_REF),
        ("overclaim_absence", cr.P7_R54_AHR_CR14_ISSUE_CREEPY_OVERCLAIM_P8_ESCAPE_REF),
        ("self_blame_non_amplification", cr.P7_R54_AHR_CR14_ISSUE_SELF_BLAME_P8_ESCAPE_REF),
    ],
)
def test_cr14_detects_risk_axis_p8_candidate_escape(axis: str, expected_issue: str) -> None:
    rows = _selection_rows()
    rows[0]["axis_scores"] = {axis_ref: 1.0 for axis_ref in cr.P7_R54_AHR_CR08_RATING_AXIS_REFS}
    rows[0]["axis_scores"][axis] = 0.10
    rows[0]["question_need_primary_class"] = "question_may_reduce_overread_risk"
    rows[0]["one_question_fit_ref"] = "fits_one_question"
    rows[0]["plan_candidate_flags"]["p8_design_material_candidate"] = True
    cr10 = _cr10_ready(rows)
    cr11 = _cr11_ready(cr10)
    cr12 = _cr12_ready(cr11)
    cr13 = _cr13_ready(cr10, cr11, cr12)
    first = cr13["question_need_observation_rows"][0]
    first["p8_design_material_candidate"] = True
    first["p8_material_candidate_reason_ref"] = "p8_material_candidate_bodyfree_only"
    first["p5_repair_required"] = False
    first["readfeel_blocker_present"] = False
    cr13["p8_material_candidate_case_refs"] = [first["case_ref_id"]]
    cr13["p8_material_candidate_case_count"] = 1

    material = _cr14_ready(cr11, cr12, cr13)
    assert material["rating_question_consistency_guard_status_ref"] == cr.P7_R54_AHR_CR14_GUARD_FAILED_STATUS_REF
    assert expected_issue in material["consistency_issue_type_counts"]
    assert material["risk_axis_p8_escape_case_count"] == 1
    assert material["next_required_step"] == cr.P7_R54_AHR_CR14_DEFAULT_BLOCKED_NEXT_REQUIRED_STEP_REF
    assert cr.assert_p7_r54_ahr_cr14_rating_question_consistency_guard_contract(material) is True


@pytest.mark.parametrize(
    "key,value",
    [
        ("schema_version", "changed"),
        ("cr11_schema_version", "changed"),
        ("cr12_schema_version", "changed"),
        ("cr13_schema_version", "changed"),
        ("rating_question_consistency_guard_allowed_status_refs", ["changed"]),
        ("rating_question_consistency_guard_status_ref", cr.P7_R54_AHR_CR14_GUARD_FAILED_STATUS_REF),
        ("rating_question_consistency_guard_evaluated", False),
        ("rating_question_consistency_guard_passed", False),
        ("rating_question_consistency_guard_reason_refs", []),
        ("rating_question_consistency_guard_step_blocker_refs", ["blocked"]),
        ("rating_question_consistency_guard_step_blocker_ref_count", 99),
        ("source_rating_row_count", 23),
        ("source_question_need_observation_row_count", 23),
        ("case_ref_id_count", 23),
        ("case_ref_ids_unique", False),
        ("consistency_issue_row_count", 1),
        ("rows_have_no_question_text", False),
        ("rating_question_consistency_guarded_here", False),
        ("actual_rating_rows_materialized_here", False),
        ("actual_question_need_observation_rows_materialized_here", False),
        ("actual_human_review_executed_by_person", False),
        ("actual_review_evidence_complete", True),
        ("actual_disposal_receipt_materialized_here", True),
        ("disposal_verified", True),
        ("question_text_materialized_here", True),
        ("p8_start_allowed", True),
        ("release_allowed", True),
        ("implemented_steps", []),
        ("not_yet_implemented_steps", []),
        ("next_required_step", "not_cr15"),
    ],
)
def test_cr14_rejects_mutations_promotion_or_evidence_completion_claims(key: str, value: object) -> None:
    mutated = deepcopy(_cr14_ready())
    mutated[key] = value
    with pytest.raises(ValueError):
        cr.assert_p7_r54_ahr_cr14_rating_question_consistency_guard_contract(mutated)


def test_cr14_rejects_issue_row_body_or_question_mutation() -> None:
    cr11, cr12, cr13 = _mutated_cr13_rating_below_target_p8_escape()
    mutated = deepcopy(_cr14_ready(cr11, cr12, cr13))
    mutated["consistency_issue_rows"][0]["question_text_included"] = True
    with pytest.raises(ValueError):
        cr.assert_p7_r54_ahr_cr14_rating_question_consistency_guard_contract(mutated)


def test_cr15_blocks_by_default_without_ready_guard_or_receipt() -> None:
    material = cr.build_p7_r54_ahr_cr15_pause_abort_expiration_disposal_receipt()

    assert set(material) == set(cr.P7_R54_AHR_CR15_DISPOSAL_RECEIPT_REQUIRED_FIELD_REFS)
    assert material["schema_version"] == cr.P7_R54_AHR_CR_DISPOSAL_RECEIPT_SCHEMA_VERSION
    assert material["operation_step_ref"] == cr.P7_R54_AHR_CR15_STEP_REF
    assert material["pause_abort_expiration_disposal_receipt_status_ref"] == cr.P7_R54_AHR_CR15_DISPOSAL_BLOCKED_STATUS_REF
    assert material["pause_abort_expiration_disposal_receipt_ready"] is False
    assert cr.P7_R54_AHR_CR15_CR14_NOT_READY_BLOCKER_REF in material[
        "pause_abort_expiration_disposal_receipt_step_blocker_refs"
    ]
    assert material["actual_disposal_receipt_materialized_here"] is False
    assert material["disposal_verified"] is False
    assert material["actual_review_evidence_complete"] is False
    assert material["next_required_step"] == cr.P7_R54_AHR_CR15_DEFAULT_BLOCKED_NEXT_REQUIRED_STEP_REF
    _assert_bodyfree_no_touch(material, allowed_true_flags=cr.P7_R54_AHR_CR15_ALLOWED_TRUE_OPERATION_FLAG_REFS)
    assert cr.assert_p7_r54_ahr_cr15_pause_abort_expiration_disposal_receipt_contract(material) is True


def test_cr15_blocks_ready_guard_when_disposal_receipt_is_missing() -> None:
    material = cr.build_p7_r54_ahr_cr15_pause_abort_expiration_disposal_receipt(
        rating_question_consistency_guard=_cr14_ready(),
    )

    assert material["pause_abort_expiration_disposal_receipt_ready"] is False
    assert cr.P7_R54_AHR_CR15_DISPOSAL_RECEIPT_MISSING_BLOCKER_REF in material[
        "pause_abort_expiration_disposal_receipt_step_blocker_refs"
    ]
    assert material["actual_disposal_receipt_materialized_here"] is False
    assert material["disposal_verified"] is False
    assert material["actual_review_evidence_complete"] is False
    assert cr.assert_p7_r54_ahr_cr15_pause_abort_expiration_disposal_receipt_contract(material) is True


def test_cr15_verifies_bodyfree_disposal_receipt_without_completing_evidence_or_release() -> None:
    material = _cr15_ready()

    assert set(material) == set(cr.P7_R54_AHR_CR15_DISPOSAL_RECEIPT_REQUIRED_FIELD_REFS)
    assert material["pause_abort_expiration_disposal_receipt_status_ref"] == cr.P7_R54_AHR_CR15_DISPOSAL_VERIFIED_STATUS_REF
    assert material["pause_abort_expiration_disposal_receipt_ready"] is True
    assert material["pause_abort_expiration_disposal_receipt_reason_refs"] == [cr.P7_R54_AHR_CR15_READY_REASON_REF]
    assert material["disposal_receipt_ref_present"] is True
    assert material["disposal_status_ref"] == "BODY_PURGED"
    assert material["body_removed"] is True
    assert material["body_removed_requirement_satisfied"] is True
    assert material["receipt_bodyfree_only"] is True
    assert material["receipt_has_no_body_path_hash"] is True
    assert material["local_only_packet_lifecycle_closed_here"] is True
    assert material["actual_rating_rows_materialized_here"] is True
    assert material["actual_question_need_observation_rows_materialized_here"] is True
    assert material["actual_disposal_receipt_materialized_here"] is True
    assert material["disposal_verified"] is True
    assert material["actual_review_evidence_complete"] is False
    assert material["p5_confirmed_final"] is False
    assert material["p6_start_allowed"] is False
    assert material["p8_start_allowed"] is False
    assert material["release_allowed"] is False
    assert tuple(material["implemented_steps"]) == cr.P7_R54_AHR_CR15_IMPLEMENTED_STEPS
    assert tuple(material["not_yet_implemented_steps"]) == cr.P7_R54_AHR_CR15_NOT_YET_IMPLEMENTED_STEPS
    assert material["next_required_step"] == cr.P7_R54_AHR_CR16_STEP_REF
    _assert_bodyfree_no_touch(material, allowed_true_flags=cr.P7_R54_AHR_CR15_ALLOWED_TRUE_OPERATION_FLAG_REFS)
    assert cr.assert_p7_r54_ahr_cr15_pause_abort_expiration_disposal_receipt_contract(material) is True


def test_cr15_allows_local_only_packet_not_materialized_receipt() -> None:
    receipt = cr.build_p7_r54_ahr_cr15_bodyfree_disposal_receipt_input(
        disposal_status_ref="LOCAL_ONLY_PACKET_NOT_MATERIALIZED",
        packet_materialized_for_review=False,
        body_removed=False,
    )
    material = _cr15_ready(receipt=receipt)

    assert material["pause_abort_expiration_disposal_receipt_ready"] is True
    assert material["disposal_status_ref"] == "LOCAL_ONLY_PACKET_NOT_MATERIALIZED"
    assert material["body_removed_required"] is False
    assert material["body_removed_requirement_satisfied"] is True
    assert material["disposal_verified"] is True
    assert cr.assert_p7_r54_ahr_cr15_pause_abort_expiration_disposal_receipt_contract(material) is True


@pytest.mark.parametrize(
    "receipt_kwargs,expected_blocker",
    [
        ({"disposal_status_ref": "DISPOSAL_FAILED"}, cr.P7_R54_AHR_CR15_DISPOSAL_FAILED_BLOCKER_REF),
        ({"disposal_status_ref": "UNKNOWN"}, cr.P7_R54_AHR_CR15_DISPOSAL_STATUS_NOT_ALLOWED_BLOCKER_REF),
        ({"body_removed": False}, cr.P7_R54_AHR_CR15_BODY_REMOVED_REQUIRED_BLOCKER_REF),
        ({"content_hash_of_body_stored": True}, cr.P7_R54_AHR_CR15_BODY_HASH_STORED_BLOCKER_REF),
        ({"body_hash_stored": True}, cr.P7_R54_AHR_CR15_BODY_HASH_STORED_BLOCKER_REF),
        ({"local_absolute_path_included": True}, cr.P7_R54_AHR_CR15_LOCAL_PATH_INCLUDED_BLOCKER_REF),
        ({"reviewer_notes_body_stored": True}, cr.P7_R54_AHR_CR15_REVIEWER_NOTES_BODY_STORED_BLOCKER_REF),
    ],
)
def test_cr15_blocks_failed_or_leaky_disposal_receipts(
    receipt_kwargs: dict[str, object], expected_blocker: str
) -> None:
    receipt = cr.build_p7_r54_ahr_cr15_bodyfree_disposal_receipt_input(**receipt_kwargs)
    material = _cr15_ready(receipt=receipt)

    assert material["pause_abort_expiration_disposal_receipt_status_ref"] == cr.P7_R54_AHR_CR15_DISPOSAL_BLOCKED_STATUS_REF
    assert material["pause_abort_expiration_disposal_receipt_ready"] is False
    assert expected_blocker in material["pause_abort_expiration_disposal_receipt_step_blocker_refs"]
    assert material["actual_disposal_receipt_materialized_here"] is False
    assert material["disposal_verified"] is False
    assert material["actual_review_evidence_complete"] is False
    assert material["next_required_step"] == cr.P7_R54_AHR_CR15_DEFAULT_BLOCKED_NEXT_REQUIRED_STEP_REF
    assert cr.assert_p7_r54_ahr_cr15_pause_abort_expiration_disposal_receipt_contract(material) is True


@pytest.mark.parametrize(
    "key,value",
    [
        ("schema_version", "changed"),
        ("cr14_schema_version", "changed"),
        ("pause_abort_expiration_disposal_receipt_allowed_status_refs", ["changed"]),
        ("pause_abort_expiration_disposal_receipt_status_ref", cr.P7_R54_AHR_CR15_DISPOSAL_BLOCKED_STATUS_REF),
        ("pause_abort_expiration_disposal_receipt_ready", False),
        ("pause_abort_expiration_disposal_receipt_reason_refs", []),
        ("pause_abort_expiration_disposal_receipt_step_blocker_refs", ["blocked"]),
        ("pause_abort_expiration_disposal_receipt_step_blocker_ref_count", 99),
        ("cr14_rating_question_consistency_guard_passed", False),
        ("disposal_receipt_input_provided", False),
        ("disposal_receipt_ref_present", False),
        ("disposal_status_allowed_refs", []),
        ("disposal_status_ref_allowed", False),
        ("body_removed_requirement_satisfied", False),
        ("content_hash_of_body_stored", True),
        ("body_hash_stored", True),
        ("local_absolute_path_included", True),
        ("reviewer_notes_body_stored", True),
        ("receipt_bodyfree_only", False),
        ("receipt_has_no_body_path_hash", False),
        ("local_only_packet_lifecycle_closed_here", False),
        ("actual_rating_rows_materialized_here", False),
        ("actual_question_need_observation_rows_materialized_here", False),
        ("actual_human_review_executed_by_person", False),
        ("actual_disposal_receipt_materialized_here", False),
        ("disposal_verified", False),
        ("actual_review_evidence_complete", True),
        ("p8_start_allowed", True),
        ("release_allowed", True),
        ("implemented_steps", []),
        ("not_yet_implemented_steps", []),
        ("next_required_step", "not_cr16"),
    ],
)
def test_cr15_rejects_mutations_promotion_or_evidence_completion_claims(key: str, value: object) -> None:
    mutated = deepcopy(_cr15_ready())
    mutated[key] = value
    with pytest.raises(ValueError):
        cr.assert_p7_r54_ahr_cr15_pause_abort_expiration_disposal_receipt_contract(mutated)


def test_cr14_cr15_alias_functions_match_primary_builders_and_contracts() -> None:
    cr10 = _cr10_ready()
    cr11 = _cr11_ready(cr10)
    cr12 = _cr12_ready(cr11)
    cr13 = _cr13_ready(cr10, cr11, cr12)
    cr14 = cr.build_p7_r54_ahr_current_received_actual_local_review_operation_rating_question_consistency_guard_bodyfree(
        rating_row_normalization=cr11,
        readfeel_execution_blocker_normalization=cr12,
        question_need_observation_normalization=cr13,
    )
    cr15 = cr.build_p7_r54_ahr_current_received_actual_local_review_operation_disposal_receipt_bodyfree(
        rating_question_consistency_guard=cr14,
        disposal_receipt_input=cr.build_p7_r54_ahr_cr15_bodyfree_disposal_receipt_input(),
    )

    assert cr.assert_p7_r54_ahr_current_received_actual_local_review_operation_rating_question_consistency_guard_bodyfree_contract(cr14) is True
    assert cr.assert_p7_r54_ahr_current_received_actual_local_review_operation_disposal_receipt_bodyfree_contract(cr15) is True
    assert cr14["operation_step_ref"] == cr.P7_R54_AHR_CR14_STEP_REF
    assert cr15["operation_step_ref"] == cr.P7_R54_AHR_CR15_STEP_REF
    assert cr14["next_required_step"] == cr.P7_R54_AHR_CR15_STEP_REF
    assert cr15["next_required_step"] == cr.P7_R54_AHR_CR16_STEP_REF
