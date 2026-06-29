# -*- coding: utf-8 -*-
"""R54-AHR-CR10/CR11 current received actual local review operation tests."""

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


def _cr10_ready() -> dict[str, object]:
    return cr.build_p7_r54_ahr_cr10_sanitized_selection_only_result_rows_intake(
        actual_local_human_review_operation_receipt=_cr09_ready(),
        selection_result_rows=_selection_rows(),
    )


def _cr11_ready() -> dict[str, object]:
    return cr.build_p7_r54_ahr_cr11_rating_row_normalization(
        sanitized_selection_only_result_rows_intake=_cr10_ready(),
    )


def test_cr10_blocks_by_default_without_ready_cr09_or_rows() -> None:
    material = cr.build_p7_r54_ahr_cr10_sanitized_selection_only_result_rows_intake()

    assert set(material) == set(cr.P7_R54_AHR_CR10_SANITIZED_SELECTION_ONLY_RESULT_ROWS_INTAKE_REQUIRED_FIELD_REFS)
    assert material["schema_version"] == cr.P7_R54_AHR_CR_SANITIZED_SELECTION_ONLY_RESULT_ROWS_INTAKE_SCHEMA_VERSION
    assert material["operation_step_ref"] == cr.P7_R54_AHR_CR10_STEP_REF
    assert material["sanitized_selection_only_result_rows_intake_status_ref"] == cr.P7_R54_AHR_CR10_SANITIZED_ROWS_BLOCKED_STATUS_REF
    assert material["sanitized_selection_only_result_rows_ready"] is False
    assert cr.P7_R54_AHR_CR10_CR09_NOT_READY_BLOCKER_REF in material["sanitized_selection_only_result_rows_blocker_refs"]
    assert cr.P7_R54_AHR_CR10_SELECTION_ROWS_INPUT_MISSING_BLOCKER_REF in material["sanitized_selection_only_result_rows_blocker_refs"]
    assert cr.P7_R54_AHR_CR10_SELECTION_ROW_COUNT_NOT_24_BLOCKER_REF in material["sanitized_selection_only_result_rows_blocker_refs"]
    assert material["review_result_rows"] == []
    assert material["sanitized_review_result_row_count"] == 0
    assert material["actual_human_review_executed_by_person"] is False
    assert material["actual_human_review_run_here"] is False
    assert material["actual_rating_rows_materialized_here"] is False
    assert material["next_required_step"] == cr.P7_R54_AHR_CR10_DEFAULT_BLOCKED_NEXT_REQUIRED_STEP_REF
    _assert_bodyfree_no_touch(material, allowed_true_flags=cr.P7_R54_AHR_CR10_ALLOWED_TRUE_OPERATION_FLAG_REFS)
    assert cr.assert_p7_r54_ahr_cr10_sanitized_selection_only_result_rows_intake_contract(material) is True


def test_cr10_accepts_24_bodyfree_selection_only_rows_without_creating_rating_or_p8() -> None:
    material = _cr10_ready()

    assert set(material) == set(cr.P7_R54_AHR_CR10_SANITIZED_SELECTION_ONLY_RESULT_ROWS_INTAKE_REQUIRED_FIELD_REFS)
    assert material["cr09_operation_receipt_ready"] is True
    assert material["cr09_actual_human_review_executed_by_person"] is True
    assert material["cr09_actual_human_review_run_here"] is True
    assert material["sanitized_selection_only_result_rows_intake_status_ref"] == cr.P7_R54_AHR_CR10_SANITIZED_ROWS_ACCEPTED_STATUS_REF
    assert material["sanitized_selection_only_result_rows_ready"] is True
    assert material["sanitized_selection_only_result_rows_reason_refs"] == [cr.P7_R54_AHR_CR10_READY_REASON_REF]
    assert material["sanitized_selection_only_result_rows_blocker_refs"] == []
    assert material["received_selection_result_row_count"] == 24
    assert material["selection_result_row_count"] == 24
    assert material["sanitized_review_result_row_count"] == 24
    assert material["case_ref_ids_unique"] is True
    assert material["blind_case_ids_unique"] is True
    assert material["packet_ref_ids_unique"] is True
    assert material["axis_refs"] == list(cr.P7_R54_AHR_CR08_RATING_AXIS_REFS)
    assert material["axis_score_count_per_row"] == 6
    assert material["rows_bodyfree_only"] is True
    assert material["rows_selection_only"] is True
    assert material["rows_have_allowed_question_observation_refs"] is True
    assert material["sanitized_selection_only_result_rows_intaken_here"] is True
    assert material["actual_sanitized_review_result_rows_intaken_here"] is True
    assert material["actual_human_review_executed_by_person"] is True
    assert material["actual_human_review_run_here"] is False
    assert material["actual_review_evidence_complete"] is False
    assert material["actual_rating_rows_materialized_here"] is False
    assert material["actual_question_need_observation_rows_materialized_here"] is False
    assert material["actual_disposal_receipt_materialized_here"] is False
    assert material["p5_confirmed_final"] is False
    assert material["p8_start_allowed"] is False
    assert material["release_allowed"] is False
    assert tuple(material["implemented_steps"]) == cr.P7_R54_AHR_CR10_IMPLEMENTED_STEPS
    assert tuple(material["not_yet_implemented_steps"]) == cr.P7_R54_AHR_CR10_NOT_YET_IMPLEMENTED_STEPS
    assert material["next_required_step"] == cr.P7_R54_AHR_CR11_STEP_REF
    for row in material["review_result_rows"]:
        assert set(row) == set(cr.P7_R54_AHR_CR10_SELECTION_RESULT_ROW_REQUIRED_FIELD_REFS)
        assert row["body_free"] is True
        assert row["selection_only"] is True
        assert row["selection_only_row"] is True
        assert set(row["axis_scores"]) == set(cr.P7_R54_AHR_CR08_RATING_AXIS_REFS)
        assert row["question_need_primary_class"] in cr.P7_R54_AHR_CR10_QUESTION_NEED_PRIMARY_CLASS_OPTION_REFS
        assert row["one_question_fit_ref"] in cr.P7_R54_AHR_CR10_ONE_QUESTION_FIT_OPTION_REFS
        assert row["plan_candidate_flags"]["p8_implementation_spec_finalized_here"] is False
    _assert_bodyfree_no_touch(material, allowed_true_flags=cr.P7_R54_AHR_CR10_ALLOWED_TRUE_OPERATION_FLAG_REFS)
    assert cr.assert_p7_r54_ahr_cr10_sanitized_selection_only_result_rows_intake_contract(material) is True


@pytest.mark.parametrize(
    "patch,expected_blocker",
    [
        (None, cr.P7_R54_AHR_CR10_SELECTION_ROW_COUNT_NOT_24_BLOCKER_REF),
        ({"case_ref_id": "not_in_manifest"}, cr.P7_R54_AHR_CR10_SELECTION_ROW_CASE_REF_NOT_IN_MANIFEST_BLOCKER_REF),
        ({"blind_case_id": "wrong_blind"}, cr.P7_R54_AHR_CR10_SELECTION_ROW_ID_MISMATCH_BLOCKER_REF),
        ({"packet_ref_id": "wrong_packet"}, cr.P7_R54_AHR_CR10_SELECTION_ROW_ID_MISMATCH_BLOCKER_REF),
        ({"operation_receipt_ref": "wrong_receipt"}, cr.P7_R54_AHR_CR10_SELECTION_ROW_OPERATION_RECEIPT_REF_MISMATCH_BLOCKER_REF),
        ({"reviewer_person_ref": "wrong_reviewer"}, cr.P7_R54_AHR_CR10_SELECTION_ROW_REVIEWER_PERSON_REF_MISMATCH_BLOCKER_REF),
        ({"review_session_id": "wrong_session"}, cr.P7_R54_AHR_CR10_SELECTION_ROW_REVIEW_SESSION_ID_MISMATCH_BLOCKER_REF),
        ({"reviewed_at_bucket_ref": ""}, cr.P7_R54_AHR_CR10_SELECTION_ROW_REVIEWED_AT_REF_MISSING_BLOCKER_REF),
        ({"axis_scores": {"history_connection_naturalness": 1.0}}, cr.P7_R54_AHR_CR10_SELECTION_ROW_AXIS_REFS_MISMATCH_BLOCKER_REF),
        ({"axis_scores": {axis: 1.2 for axis in cr.P7_R54_AHR_CR08_RATING_AXIS_REFS}}, cr.P7_R54_AHR_CR10_SELECTION_ROW_AXIS_REFS_MISMATCH_BLOCKER_REF),
        ({"verdict": "UNKNOWN"}, cr.P7_R54_AHR_CR10_SELECTION_ROW_VERDICT_NOT_ALLOWED_BLOCKER_REF),
        ({"question_need_primary_class": "unknown"}, cr.P7_R54_AHR_CR10_SELECTION_ROW_OPTION_NOT_ALLOWED_BLOCKER_REF),
        ({"one_question_fit_ref": "unknown"}, cr.P7_R54_AHR_CR10_SELECTION_ROW_OPTION_NOT_ALLOWED_BLOCKER_REF),
        ({"selection_only": False}, cr.P7_R54_AHR_CR10_SELECTION_ROW_SELECTION_ONLY_FALSE_BLOCKER_REF),
        ({"body_free": False}, cr.P7_R54_AHR_CR10_SELECTION_ROW_BODY_FREE_FALSE_BLOCKER_REF),
        ({"question_text": "must not be exported"}, cr.P7_R54_AHR_CR10_SELECTION_ROW_FORBIDDEN_KEY_BLOCKER_REF),
    ],
)
def test_cr10_blocks_invalid_or_unsafe_selection_rows(
    patch: dict[str, object] | None, expected_blocker: str
) -> None:
    rows = _selection_rows()
    if patch is None:
        rows = rows[:-1]
    else:
        rows[0].update(patch)
    material = cr.build_p7_r54_ahr_cr10_sanitized_selection_only_result_rows_intake(
        actual_local_human_review_operation_receipt=_cr09_ready(),
        selection_result_rows=rows,
    )

    assert material["sanitized_selection_only_result_rows_ready"] is False
    assert expected_blocker in material["sanitized_selection_only_result_rows_blocker_refs"]
    assert material["review_result_rows"] == []
    assert material["actual_sanitized_review_result_rows_intaken_here"] is False
    assert material["actual_rating_rows_materialized_here"] is False
    assert material["next_required_step"] == cr.P7_R54_AHR_CR10_DEFAULT_BLOCKED_NEXT_REQUIRED_STEP_REF
    assert cr.assert_p7_r54_ahr_cr10_sanitized_selection_only_result_rows_intake_contract(material) is True


def test_cr10_blocks_when_cr09_operation_receipt_is_not_ready_even_with_valid_rows() -> None:
    material = cr.build_p7_r54_ahr_cr10_sanitized_selection_only_result_rows_intake(
        actual_local_human_review_operation_receipt=cr.build_p7_r54_ahr_cr09_actual_local_human_review_operation_receipt(
            reviewer_selection_form=_cr08_ready()
        ),
        selection_result_rows=_selection_rows(),
    )

    assert material["cr09_operation_receipt_ready"] is False
    assert material["sanitized_selection_only_result_rows_ready"] is False
    assert cr.P7_R54_AHR_CR10_CR09_NOT_READY_BLOCKER_REF in material["sanitized_selection_only_result_rows_blocker_refs"]
    assert material["actual_human_review_executed_by_person"] is False
    assert cr.assert_p7_r54_ahr_cr10_sanitized_selection_only_result_rows_intake_contract(material) is True


@pytest.mark.parametrize(
    "key,value",
    [
        ("schema_version", "changed"),
        ("cr09_schema_version", "changed"),
        ("cr09_next_required_step", "not_cr10"),
        ("sanitized_selection_only_result_rows_allowed_status_refs", ["changed"]),
        ("sanitized_selection_only_result_rows_intake_status_ref", cr.P7_R54_AHR_CR10_SANITIZED_ROWS_BLOCKED_STATUS_REF),
        ("sanitized_selection_only_result_rows_ready", False),
        ("sanitized_selection_only_result_rows_reason_refs", []),
        ("sanitized_selection_only_result_rows_blocker_refs", ["blocked"]),
        ("sanitized_selection_only_result_rows_blocker_ref_count", 99),
        ("received_selection_result_row_count", 23),
        ("selection_result_row_count", 23),
        ("sanitized_review_result_row_count", 23),
        ("case_ref_ids_unique", False),
        ("axis_refs", []),
        ("rating_axis_target_thresholds", {}),
        ("actual_human_review_executed_by_person", False),
        ("actual_human_review_run_here", True),
        ("actual_review_evidence_complete", True),
        ("actual_rating_rows_materialized_here", True),
        ("actual_question_need_observation_rows_materialized_here", True),
        ("actual_disposal_receipt_materialized_here", True),
        ("p5_confirmed_final", True),
        ("p8_start_allowed", True),
        ("release_allowed", True),
        ("implemented_steps", []),
        ("not_yet_implemented_steps", []),
        ("next_required_step", "not_cr11"),
    ],
)
def test_cr10_rejects_mutations_promotion_or_boundary_claims(key: str, value: object) -> None:
    mutated = deepcopy(_cr10_ready())
    mutated[key] = value
    with pytest.raises(ValueError):
        cr.assert_p7_r54_ahr_cr10_sanitized_selection_only_result_rows_intake_contract(mutated)


def test_cr10_rejects_forbidden_body_or_question_key_in_material() -> None:
    mutated = deepcopy(_cr10_ready())
    mutated["question_text"] = "must not be exported"
    with pytest.raises(ValueError):
        cr.assert_p7_r54_ahr_cr10_sanitized_selection_only_result_rows_intake_contract(mutated)


def test_cr11_blocks_by_default_without_ready_cr10_rows() -> None:
    material = cr.build_p7_r54_ahr_cr11_rating_row_normalization()

    assert set(material) == set(cr.P7_R54_AHR_CR11_RATING_ROW_NORMALIZATION_REQUIRED_FIELD_REFS)
    assert material["schema_version"] == cr.P7_R54_AHR_CR_RATING_ROW_NORMALIZATION_SCHEMA_VERSION
    assert material["operation_step_ref"] == cr.P7_R54_AHR_CR11_STEP_REF
    assert material["rating_row_normalization_status_ref"] == cr.P7_R54_AHR_CR11_RATING_ROWS_BLOCKED_STATUS_REF
    assert material["rating_row_normalization_ready"] is False
    assert cr.P7_R54_AHR_CR11_CR10_NOT_READY_BLOCKER_REF in material["rating_row_normalization_blocker_refs"]
    assert material["rating_rows"] == []
    assert material["rating_row_count"] == 0
    assert material["actual_rating_rows_materialized_here"] is False
    assert material["actual_review_evidence_complete"] is False
    assert material["next_required_step"] == cr.P7_R54_AHR_CR11_DEFAULT_BLOCKED_NEXT_REQUIRED_STEP_REF
    _assert_bodyfree_no_touch(material, allowed_true_flags=cr.P7_R54_AHR_CR11_ALLOWED_TRUE_OPERATION_FLAG_REFS)
    assert cr.assert_p7_r54_ahr_cr11_rating_row_normalization_contract(material) is True


def test_cr11_normalizes_rating_rows_without_question_rows_disposal_or_release() -> None:
    material = _cr11_ready()

    assert set(material) == set(cr.P7_R54_AHR_CR11_RATING_ROW_NORMALIZATION_REQUIRED_FIELD_REFS)
    assert material["cr10_sanitized_selection_only_result_rows_intake_status_ref"] == cr.P7_R54_AHR_CR10_SANITIZED_ROWS_ACCEPTED_STATUS_REF
    assert material["cr10_rating_row_normalization_allowed_next"] is True
    assert material["rating_row_normalization_status_ref"] == cr.P7_R54_AHR_CR11_RATING_ROWS_NORMALIZED_STATUS_REF
    assert material["rating_row_normalization_ready"] is True
    assert material["rating_row_normalization_reason_refs"] == [cr.P7_R54_AHR_CR11_READY_REASON_REF]
    assert material["rating_row_normalization_blocker_refs"] == []
    assert material["source_sanitized_review_result_row_count"] == 24
    assert material["rating_row_count"] == 24
    assert material["rating_row_ref_count"] == 24
    assert material["source_review_result_row_ref_count"] == 24
    assert material["case_ref_ids_unique"] is True
    assert material["blind_case_ids_unique"] is True
    assert material["packet_ref_ids_unique"] is True
    assert material["axis_refs"] == list(cr.P7_R54_AHR_CR08_RATING_AXIS_REFS)
    assert material["axis_score_count_per_row"] == 6
    assert material["average_axis_scores_present"] is True
    assert all(value == 1.0 for value in material["average_axis_scores"].values())
    assert material["overall_average_axis_score"] == 1.0
    assert material["below_target_case_count"] == 0
    assert material["pass_case_count"] == 24
    assert material["rating_rows_bodyfree_only"] is True
    assert material["rating_rows_normalized_here"] is True
    assert material["actual_rating_rows_materialized_here"] is True
    assert material["actual_human_review_executed_by_person"] is True
    assert material["actual_human_review_run_here"] is False
    assert material["actual_review_evidence_complete"] is False
    assert material["actual_question_need_observation_rows_materialized_here"] is False
    assert material["actual_disposal_receipt_materialized_here"] is False
    assert material["p5_confirmed_final"] is False
    assert material["p8_start_allowed"] is False
    assert material["release_allowed"] is False
    assert tuple(material["implemented_steps"]) == cr.P7_R54_AHR_CR11_IMPLEMENTED_STEPS
    assert tuple(material["not_yet_implemented_steps"]) == cr.P7_R54_AHR_CR11_NOT_YET_IMPLEMENTED_STEPS
    assert material["next_required_step"] == cr.P7_R54_AHR_CR12_STEP_REF
    for row in material["rating_rows"]:
        assert set(row) == set(cr.P7_R54_AHR_CR11_RATING_ROW_REQUIRED_FIELD_REFS)
        assert row["schema_version"] == cr.P7_R54_AHR_CR11_RATING_ROW_SCHEMA_VERSION
        assert row["body_free"] is True
        assert set(row["axis_scores"]) == set(cr.P7_R54_AHR_CR08_RATING_AXIS_REFS)
        assert row["axis_targets"] == cr.P7_R54_AHR_CR08_RATING_AXIS_TARGET_THRESHOLDS
        assert set(row["axis_pass_flags"]) == set(cr.P7_R54_AHR_CR08_RATING_AXIS_REFS)
        assert row["verdict"] in cr.P7_R54_AHR_CR10_VERDICT_OPTION_REFS
    _assert_bodyfree_no_touch(material, allowed_true_flags=cr.P7_R54_AHR_CR11_ALLOWED_TRUE_OPERATION_FLAG_REFS)
    assert cr.assert_p7_r54_ahr_cr11_rating_row_normalization_contract(material) is True


def test_cr11_preserves_below_target_axis_refs_without_repair_or_p8_promotion() -> None:
    rows = _selection_rows()
    rows[0]["axis_scores"] = {axis: 1.0 for axis in cr.P7_R54_AHR_CR08_RATING_AXIS_REFS}
    rows[0]["axis_scores"]["creepy_absence"] = 0.5
    cr10 = cr.build_p7_r54_ahr_cr10_sanitized_selection_only_result_rows_intake(
        actual_local_human_review_operation_receipt=_cr09_ready(),
        selection_result_rows=rows,
    )
    material = cr.build_p7_r54_ahr_cr11_rating_row_normalization(
        sanitized_selection_only_result_rows_intake=cr10,
    )

    assert material["rating_row_normalization_ready"] is True
    assert material["below_target_case_count"] == 1
    assert material["below_target_axis_ref_counts"]["creepy_absence"] == 1
    assert material["rating_rows"][0]["below_target_axis_refs"] == ["creepy_absence"]
    assert material["rating_rows"][0]["axis_pass_flags"]["creepy_absence"] is False
    assert material["p8_start_allowed"] is False
    assert material["p5_confirmed_final"] is False
    assert cr.assert_p7_r54_ahr_cr11_rating_row_normalization_contract(material) is True


def test_cr11_blocks_when_cr10_sanitized_rows_are_not_ready() -> None:
    cr10_blocked = cr.build_p7_r54_ahr_cr10_sanitized_selection_only_result_rows_intake(
        actual_local_human_review_operation_receipt=_cr09_ready(),
        selection_result_rows=_selection_rows()[:-1],
    )
    material = cr.build_p7_r54_ahr_cr11_rating_row_normalization(
        sanitized_selection_only_result_rows_intake=cr10_blocked,
    )

    assert material["rating_row_normalization_ready"] is False
    assert cr.P7_R54_AHR_CR11_CR10_NOT_READY_BLOCKER_REF in material["rating_row_normalization_blocker_refs"]
    assert material["rating_rows"] == []
    assert material["actual_rating_rows_materialized_here"] is False
    assert cr.assert_p7_r54_ahr_cr11_rating_row_normalization_contract(material) is True


@pytest.mark.parametrize(
    "key,value",
    [
        ("schema_version", "changed"),
        ("cr10_schema_version", "changed"),
        ("cr10_next_required_step", "not_cr11"),
        ("rating_row_normalization_allowed_status_refs", ["changed"]),
        ("rating_row_normalization_status_ref", cr.P7_R54_AHR_CR11_RATING_ROWS_BLOCKED_STATUS_REF),
        ("rating_row_normalization_ready", False),
        ("rating_row_normalization_reason_refs", []),
        ("rating_row_normalization_blocker_refs", ["blocked"]),
        ("rating_row_normalization_blocker_ref_count", 99),
        ("source_sanitized_review_result_row_count", 23),
        ("rating_row_count", 23),
        ("rating_row_ref_count", 23),
        ("axis_refs", []),
        ("rating_axis_target_thresholds", {}),
        ("average_axis_scores_present", False),
        ("rating_rows_bodyfree_only", False),
        ("rating_rows_normalized_here", False),
        ("actual_rating_rows_materialized_here", False),
        ("actual_human_review_executed_by_person", False),
        ("actual_human_review_run_here", True),
        ("actual_review_evidence_complete", True),
        ("actual_question_need_observation_rows_materialized_here", True),
        ("actual_disposal_receipt_materialized_here", True),
        ("p5_confirmed_final", True),
        ("p8_start_allowed", True),
        ("release_allowed", True),
        ("implemented_steps", []),
        ("not_yet_implemented_steps", []),
        ("next_required_step", "not_cr12"),
    ],
)
def test_cr11_rejects_mutations_promotion_or_evidence_completion_claims(key: str, value: object) -> None:
    mutated = deepcopy(_cr11_ready())
    mutated[key] = value
    with pytest.raises(ValueError):
        cr.assert_p7_r54_ahr_cr11_rating_row_normalization_contract(mutated)


@pytest.mark.parametrize(
    "row_patch",
    [
        {"body_free": False},
        {"axis_targets": {}},
        {"axis_scores": {"history_connection_naturalness": 1.0}},
        {"axis_score_count": 23},
        {"verdict": "UNKNOWN"},
    ],
)
def test_cr11_rejects_rating_row_mutations(row_patch: dict[str, object]) -> None:
    mutated = deepcopy(_cr11_ready())
    mutated["rating_rows"][0].update(row_patch)
    with pytest.raises(ValueError):
        cr.assert_p7_r54_ahr_cr11_rating_row_normalization_contract(mutated)


def test_cr11_rejects_forbidden_body_or_question_key_in_material() -> None:
    mutated = deepcopy(_cr11_ready())
    mutated["rating_rows"][0]["question_text"] = "must not be exported"
    with pytest.raises(ValueError):
        cr.assert_p7_r54_ahr_cr11_rating_row_normalization_contract(mutated)


def test_cr10_cr11_alias_functions_match_primary_builders_and_contracts() -> None:
    cr10 = cr.build_p7_r54_ahr_current_received_actual_local_review_operation_sanitized_selection_only_result_rows_intake_bodyfree(
        actual_local_human_review_operation_receipt=_cr09_ready(),
        selection_result_rows=_selection_rows(),
    )
    cr11 = cr.build_p7_r54_ahr_current_received_actual_local_review_operation_rating_row_normalization_bodyfree(
        sanitized_selection_only_result_rows_intake=cr10,
    )

    assert cr.assert_p7_r54_ahr_current_received_actual_local_review_operation_sanitized_selection_only_result_rows_intake_bodyfree_contract(cr10) is True
    assert cr.assert_p7_r54_ahr_current_received_actual_local_review_operation_rating_row_normalization_bodyfree_contract(cr11) is True
    assert cr10["operation_step_ref"] == cr.P7_R54_AHR_CR10_STEP_REF
    assert cr11["operation_step_ref"] == cr.P7_R54_AHR_CR11_STEP_REF
    assert cr10["next_required_step"] == cr.P7_R54_AHR_CR11_STEP_REF
    assert cr11["next_required_step"] == cr.P7_R54_AHR_CR12_STEP_REF
