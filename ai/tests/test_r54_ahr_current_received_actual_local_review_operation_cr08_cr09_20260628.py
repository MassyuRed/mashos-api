# -*- coding: utf-8 -*-
"""R54-AHR-CR08/CR09 current received actual local review operation tests."""

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


def test_cr08_blocks_by_default_before_packet_receipt_and_reviewer_person_confirmation() -> None:
    material = cr.build_p7_r54_ahr_cr08_reviewer_selection_form()

    assert set(material) == set(cr.P7_R54_AHR_CR08_REVIEWER_SELECTION_FORM_REQUIRED_FIELD_REFS)
    assert material["schema_version"] == cr.P7_R54_AHR_CR_REVIEWER_SELECTION_FORM_SCHEMA_VERSION
    assert material["policy_section"] == cr.P7_R54_AHR_CR08_STEP_REF
    assert material["operation_step_ref"] == cr.P7_R54_AHR_CR08_STEP_REF
    assert material["cr07_schema_version"] == cr.P7_R54_AHR_CR_PACKET_GENERATION_RECEIPT_SCAN_SCHEMA_VERSION
    assert material["cr07_packet_generation_receipt_ready"] is False
    assert material["cr07_packet_generation_receipt_ref_present"] is False

    assert material["reviewer_selection_form_status_ref"] == cr.P7_R54_AHR_CR08_REVIEWER_FORM_BLOCKED_STATUS_REF
    assert tuple(material["reviewer_selection_form_allowed_status_refs"]) == cr.P7_R54_AHR_CR08_ALLOWED_REVIEWER_FORM_STATUS_REFS
    assert material["reviewer_selection_form_ready"] is False
    assert material["reviewer_selection_form_reason_refs"] == []
    assert cr.P7_R54_AHR_CR08_CR07_NOT_READY_BLOCKER_REF in material["reviewer_selection_form_blocker_refs"]
    assert cr.P7_R54_AHR_CR08_CR07_RECEIPT_REF_MISSING_BLOCKER_REF in material["reviewer_selection_form_blocker_refs"]
    assert cr.P7_R54_AHR_CR08_REVIEWER_PERSON_REF_MISSING_BLOCKER_REF in material["reviewer_selection_form_blocker_refs"]
    assert cr.P7_R54_AHR_CR08_REVIEWER_IS_PERSON_FALSE_BLOCKER_REF in material["reviewer_selection_form_blocker_refs"]
    assert cr.P7_R54_AHR_CR08_REVIEWER_PERSON_NOT_CONFIRMED_BLOCKER_REF in material["reviewer_selection_form_blocker_refs"]
    assert material["reviewer_person_ref"] == ""
    assert material["reviewer_person_ref_present"] is False
    assert material["reviewer_is_person"] is False
    assert material["reviewer_person_confirmed"] is False
    assert material["reviewer_person_boundary_confirmed"] is False
    assert material["next_required_step"] == cr.P7_R54_AHR_CR08_DEFAULT_BLOCKED_NEXT_REQUIRED_STEP_REF
    _assert_bodyfree_no_touch(material)
    assert cr.assert_p7_r54_ahr_cr08_reviewer_selection_form_contract(material) is True


def test_cr08_ready_form_freezes_selection_only_person_boundary_without_running_review() -> None:
    material = _cr08_ready()

    assert set(material) == set(cr.P7_R54_AHR_CR08_REVIEWER_SELECTION_FORM_REQUIRED_FIELD_REFS)
    assert material["cr07_packet_generation_receipt_ready"] is True
    assert material["cr07_packet_generation_receipt_ref_present"] is True
    assert material["cr07_packet_case_count"] == 24
    assert material["cr07_packet_completeness_passed"] is True
    assert material["cr07_export_denylist_scan_passed"] is True
    assert material["cr07_body_full_packet_content_included"] is False
    assert material["cr07_local_absolute_path_included"] is False
    assert material["cr07_body_hash_included"] is False

    assert material["reviewer_selection_form_status_ref"] == cr.P7_R54_AHR_CR08_REVIEWER_FORM_READY_STATUS_REF
    assert material["reviewer_selection_form_ready"] is True
    assert material["reviewer_selection_form_reason_refs"] == [cr.P7_R54_AHR_CR08_READY_REASON_REF]
    assert material["reviewer_selection_form_blocker_refs"] == []
    assert material["reviewer_person_ref"] == cr.P7_R54_AHR_CR08_DEFAULT_REVIEWER_PERSON_REF
    assert material["reviewer_person_ref_present"] is True
    assert material["reviewer_is_person"] is True
    assert material["reviewer_person_confirmed"] is True
    assert material["reviewer_person_boundary_confirmed"] is True
    assert material["reviewer_identity_bodyfree_ref_only"] is True

    assert tuple(material["rating_axis_refs"]) == cr.P7_R54_AHR_CR08_RATING_AXIS_REFS
    assert material["rating_axis_count"] == 6
    assert material["rating_axis_target_thresholds"] == cr.P7_R54_AHR_CR08_RATING_AXIS_TARGET_THRESHOLDS
    assert tuple(material["question_need_primary_class_options"]) == cr.P7_R54_AHR_CR08_QUESTION_NEED_PRIMARY_CLASS_OPTION_REFS
    assert material["question_need_primary_class_option_count"] == 9
    assert tuple(material["one_question_fit_option_refs"]) == cr.P7_R54_AHR_CR08_ONE_QUESTION_FIT_OPTION_REFS
    assert material["one_question_fit_option_count"] == 7
    assert material["selection_row_count_required"] == 24
    assert material["allowed_selection_row_count"] == 24
    assert material["selection_only"] is True
    assert material["free_text_allowed"] is False
    assert material["reviewer_free_text_allowed"] is False
    assert material["reviewer_notes_export_allowed"] is False
    assert material["question_text_allowed"] is False
    assert material["draft_question_text_allowed"] is False
    assert material["selection_form_does_not_execute_actual_human_review"] is True
    assert material["selection_form_does_not_create_review_rows"] is True
    assert material["selection_form_does_not_create_disposal_receipt"] is True
    assert material["actual_human_review_run_here"] is False
    assert tuple(material["implemented_steps"]) == cr.P7_R54_AHR_CR08_IMPLEMENTED_STEPS
    assert tuple(material["not_yet_implemented_steps"]) == cr.P7_R54_AHR_CR08_NOT_YET_IMPLEMENTED_STEPS
    assert material["next_required_step"] == cr.P7_R54_AHR_CR09_STEP_REF
    _assert_bodyfree_no_touch(material)
    assert cr.assert_p7_r54_ahr_cr08_reviewer_selection_form_contract(material) is True


@pytest.mark.parametrize(
    "kwargs,expected_blocker",
    [
        ({"reviewer_person_ref": ""}, cr.P7_R54_AHR_CR08_REVIEWER_PERSON_REF_MISSING_BLOCKER_REF),
        ({"reviewer_is_person": False}, cr.P7_R54_AHR_CR08_REVIEWER_IS_PERSON_FALSE_BLOCKER_REF),
        ({"reviewer_person_confirmed": False}, cr.P7_R54_AHR_CR08_REVIEWER_PERSON_NOT_CONFIRMED_BLOCKER_REF),
    ],
)
def test_cr08_blocks_when_reviewer_person_boundary_is_not_confirmed(
    kwargs: dict[str, object], expected_blocker: str
) -> None:
    params: dict[str, object] = {
        "packet_generation_receipt_scan": _cr07_ready(),
        "reviewer_person_ref": cr.P7_R54_AHR_CR08_DEFAULT_REVIEWER_PERSON_REF,
        "reviewer_is_person": True,
        "reviewer_person_confirmed": True,
    }
    params.update(kwargs)
    material = cr.build_p7_r54_ahr_cr08_reviewer_selection_form(**params)

    assert material["reviewer_selection_form_ready"] is False
    assert expected_blocker in material["reviewer_selection_form_blocker_refs"]
    assert material["reviewer_person_ref_present"] is False
    assert material["reviewer_is_person"] is False
    assert material["reviewer_person_confirmed"] is False
    assert material["actual_human_review_run_here"] is False
    assert material["next_required_step"] == cr.P7_R54_AHR_CR08_DEFAULT_BLOCKED_NEXT_REQUIRED_STEP_REF
    assert cr.assert_p7_r54_ahr_cr08_reviewer_selection_form_contract(material) is True


@pytest.mark.parametrize(
    "key,value",
    [
        ("cr07_schema_version", "changed"),
        ("cr07_next_required_step", "not_cr08"),
        ("cr07_packet_generation_receipt_ready", False),
        ("cr07_packet_generation_receipt_ref_present", False),
        ("cr07_packet_case_count", 23),
        ("cr07_packet_completeness_passed", False),
        ("cr07_export_denylist_scan_passed", False),
        ("cr07_body_full_packet_content_included", True),
        ("cr07_local_absolute_path_included", True),
        ("cr07_body_hash_included", True),
        ("cr07_actual_human_review_run_here", True),
        ("reviewer_selection_form_allowed_status_refs", ["changed"]),
        ("reviewer_selection_form_status_ref", cr.P7_R54_AHR_CR08_REVIEWER_FORM_BLOCKED_STATUS_REF),
        ("reviewer_selection_form_ready", False),
        ("reviewer_selection_form_reason_refs", []),
        ("reviewer_selection_form_blocker_refs", ["blocked"]),
        ("reviewer_selection_form_blocker_ref_count", 99),
        ("reviewer_person_ref", ""),
        ("reviewer_person_ref_present", False),
        ("reviewer_is_person", False),
        ("reviewer_person_confirmed", False),
        ("reviewer_person_boundary_confirmed", False),
        ("reviewer_identity_bodyfree_ref_only", False),
        ("rating_axis_refs", []),
        ("rating_axis_count", 99),
        ("rating_axis_target_thresholds", {}),
        ("question_need_primary_class_options", []),
        ("question_need_primary_class_option_count", 99),
        ("one_question_fit_option_refs", []),
        ("one_question_fit_option_count", 99),
        ("selection_row_count_required", 23),
        ("allowed_selection_row_count", 23),
        ("selection_only", False),
        ("free_text_allowed", True),
        ("reviewer_free_text_allowed", True),
        ("reviewer_notes_export_allowed", True),
        ("question_text_allowed", True),
        ("draft_question_text_allowed", True),
        ("selection_form_does_not_execute_actual_human_review", False),
        ("selection_form_does_not_create_review_rows", False),
        ("selection_form_does_not_create_disposal_receipt", False),
        ("actual_human_review_run_here", True),
        ("actual_review_evidence_complete", True),
        ("actual_rating_rows_materialized_here", True),
        ("actual_question_need_observation_rows_materialized_here", True),
        ("actual_disposal_receipt_materialized_here", True),
        ("p5_confirmed_final", True),
        ("p6_start_allowed", True),
        ("p8_start_allowed", True),
        ("release_allowed", True),
        ("implemented_steps", []),
        ("not_yet_implemented_steps", []),
        ("next_required_step", "not_cr09"),
    ],
)
def test_cr08_rejects_form_mutations_execution_or_promotion(key: str, value: object) -> None:
    mutated = deepcopy(_cr08_ready())
    mutated[key] = value
    with pytest.raises(ValueError):
        cr.assert_p7_r54_ahr_cr08_reviewer_selection_form_contract(mutated)


def test_cr08_rejects_forbidden_body_or_question_key_in_material() -> None:
    mutated = deepcopy(_cr08_ready())
    mutated["question_text"] = "must not be exported"
    with pytest.raises(ValueError):
        cr.assert_p7_r54_ahr_cr08_reviewer_selection_form_contract(mutated)


def test_cr09_blocks_without_operation_receipt_input_even_when_cr08_is_ready() -> None:
    material = cr.build_p7_r54_ahr_cr09_actual_local_human_review_operation_receipt(
        reviewer_selection_form=_cr08_ready()
    )

    assert set(material) == set(cr.P7_R54_AHR_CR09_ACTUAL_LOCAL_HUMAN_REVIEW_OPERATION_RECEIPT_REQUIRED_FIELD_REFS)
    assert material["schema_version"] == cr.P7_R54_AHR_CR_ACTUAL_LOCAL_HUMAN_REVIEW_OPERATION_RECEIPT_SCHEMA_VERSION
    assert material["policy_section"] == cr.P7_R54_AHR_CR09_STEP_REF
    assert material["operation_step_ref"] == cr.P7_R54_AHR_CR09_STEP_REF
    assert material["cr08_schema_version"] == cr.P7_R54_AHR_CR_REVIEWER_SELECTION_FORM_SCHEMA_VERSION
    assert material["cr08_reviewer_selection_form_ready"] is True
    assert material["cr08_reviewer_person_ref_present"] is True

    assert material["operation_receipt_status_ref"] == cr.P7_R54_AHR_CR09_OPERATION_RECEIPT_BLOCKED_STATUS_REF
    assert tuple(material["operation_receipt_allowed_status_refs"]) == cr.P7_R54_AHR_CR09_ALLOWED_OPERATION_RECEIPT_STATUS_REFS
    assert material["operation_receipt_ready"] is False
    assert material["operation_receipt_reason_refs"] == []
    assert material["operation_receipt_blocker_refs"] == [cr.P7_R54_AHR_CR09_OPERATION_RECEIPT_INPUT_MISSING_BLOCKER_REF]
    assert material["operation_receipt_blocker_ref_count"] == 1
    assert material["operation_receipt_input_provided"] is False
    assert material["operation_receipt_ref"] == ""
    assert material["operation_receipt_ref_present"] is False
    assert material["reviewer_person_ref"] == ""
    assert material["reviewer_person_ref_matches_cr08"] is False
    assert material["actual_human_review_executed_by_person"] is False
    assert material["actual_human_review_run_here"] is False
    assert material["actual_human_review_operation_run"] is False
    assert material["actual_review_evidence_complete"] is False
    assert material["next_required_step"] == cr.P7_R54_AHR_CR09_DEFAULT_BLOCKED_NEXT_REQUIRED_STEP_REF
    _assert_bodyfree_no_touch(material, allowed_true_flags=cr.P7_R54_AHR_CR09_ALLOWED_TRUE_OPERATION_FLAG_REFS)
    assert cr.assert_p7_r54_ahr_cr09_actual_local_human_review_operation_receipt_contract(material) is True


def test_cr09_accepts_bodyfree_person_executed_local_review_receipt_but_not_evidence_complete() -> None:
    material = _cr09_ready()

    assert set(material) == set(cr.P7_R54_AHR_CR09_ACTUAL_LOCAL_HUMAN_REVIEW_OPERATION_RECEIPT_REQUIRED_FIELD_REFS)
    assert material["cr08_reviewer_selection_form_ready"] is True
    assert material["cr08_reviewer_person_ref"] == cr.P7_R54_AHR_CR08_DEFAULT_REVIEWER_PERSON_REF
    assert material["cr08_reviewer_is_person"] is True
    assert material["cr08_reviewer_person_confirmed"] is True
    assert material["cr08_selection_row_count_required"] == 24
    assert material["cr08_selection_only"] is True
    assert material["cr08_free_text_allowed"] is False
    assert material["cr08_question_text_allowed"] is False

    assert material["operation_receipt_status_ref"] == cr.P7_R54_AHR_CR09_OPERATION_RECEIPT_ACCEPTED_STATUS_REF
    assert material["operation_receipt_ready"] is True
    assert material["operation_receipt_reason_refs"] == [cr.P7_R54_AHR_CR09_READY_REASON_REF]
    assert material["operation_receipt_blocker_refs"] == []
    assert material["operation_receipt_input_provided"] is True
    assert material["operation_receipt_input_forbidden_key_detected"] is False
    assert material["operation_receipt_ref"] == cr.P7_R54_AHR_CR09_DEFAULT_OPERATION_RECEIPT_REF
    assert material["operation_receipt_ref_present"] is True
    assert material["reviewer_person_ref"] == cr.P7_R54_AHR_CR08_DEFAULT_REVIEWER_PERSON_REF
    assert material["reviewer_person_ref_matches_cr08"] is True
    assert material["reviewer_is_person"] is True
    assert material["reviewer_person_confirmed"] is True
    assert material["reviewer_local_only_read_receipt_present"] is True
    assert material["actual_human_review_executed_by_person"] is True
    assert material["review_started_at_bucket_ref"] == cr.P7_R54_AHR_CR09_DEFAULT_REVIEW_STARTED_AT_BUCKET_REF
    assert material["review_started_at_bucket_ref_present"] is True
    assert material["review_completed_at_bucket_ref"] == cr.P7_R54_AHR_CR09_DEFAULT_REVIEW_COMPLETED_AT_BUCKET_REF
    assert material["review_completed_at_bucket_ref_present"] is True
    assert material["reviewed_case_count"] == 24
    assert material["reviewed_case_count_matches_manifest"] is True
    assert material["selection_row_count"] == 24
    assert material["selection_row_count_matches_required"] is True
    assert material["local_only"] is True
    assert material["must_not_export"] is True
    assert material["selection_only"] is True
    assert material["actual_human_review_run_here"] is True
    assert material["actual_human_review_operation_run"] is True

    assert material["actual_human_review_complete"] is False
    assert material["actual_review_evidence_complete"] is False
    assert material["actual_rating_rows_materialized_here"] is False
    assert material["actual_question_need_observation_rows_materialized_here"] is False
    assert material["actual_disposal_receipt_materialized_here"] is False
    assert material["disposal_verified"] is False
    assert material["p5_confirmed_final"] is False
    assert material["p6_start_allowed"] is False
    assert material["p8_start_allowed"] is False
    assert material["release_allowed"] is False
    assert tuple(material["implemented_steps"]) == cr.P7_R54_AHR_CR09_IMPLEMENTED_STEPS
    assert tuple(material["not_yet_implemented_steps"]) == cr.P7_R54_AHR_CR09_NOT_YET_IMPLEMENTED_STEPS
    assert material["next_required_step"] == cr.P7_R54_AHR_CR10_STEP_REF
    _assert_bodyfree_no_touch(material, allowed_true_flags=cr.P7_R54_AHR_CR09_ALLOWED_TRUE_OPERATION_FLAG_REFS)
    assert cr.assert_p7_r54_ahr_cr09_actual_local_human_review_operation_receipt_contract(material) is True


@pytest.mark.parametrize(
    "receipt_patch,expected_blocker",
    [
        ({"operation_receipt_ref": ""}, cr.P7_R54_AHR_CR09_OPERATION_RECEIPT_REF_MISSING_BLOCKER_REF),
        ({"reviewer_person_ref": "different_reviewer"}, cr.P7_R54_AHR_CR09_REVIEWER_PERSON_REF_MISMATCH_BLOCKER_REF),
        ({"reviewer_local_only_read_receipt_present": False}, cr.P7_R54_AHR_CR09_REVIEWER_LOCAL_ONLY_READ_RECEIPT_MISSING_BLOCKER_REF),
        ({"review_started_at_bucket_ref": ""}, cr.P7_R54_AHR_CR09_REVIEW_STARTED_BUCKET_REF_MISSING_BLOCKER_REF),
        ({"review_completed_at_bucket_ref": ""}, cr.P7_R54_AHR_CR09_REVIEW_COMPLETED_BUCKET_REF_MISSING_BLOCKER_REF),
        ({"reviewed_case_count": 23}, cr.P7_R54_AHR_CR09_REVIEWED_CASE_COUNT_NOT_24_BLOCKER_REF),
        ({"reviewed_case_count": "not-an-int"}, cr.P7_R54_AHR_CR09_REVIEWED_CASE_COUNT_NOT_24_BLOCKER_REF),
        ({"selection_row_count": 23}, cr.P7_R54_AHR_CR09_SELECTION_ROW_COUNT_NOT_24_BLOCKER_REF),
        ({"local_only": False}, cr.P7_R54_AHR_CR09_LOCAL_ONLY_FALSE_BLOCKER_REF),
        ({"must_not_export": False}, cr.P7_R54_AHR_CR09_MUST_NOT_EXPORT_FALSE_BLOCKER_REF),
        ({"selection_only": False}, cr.P7_R54_AHR_CR09_SELECTION_ONLY_FALSE_BLOCKER_REF),
        ({"local_absolute_path": "/tmp/body-full"}, cr.P7_R54_AHR_CR09_FORBIDDEN_RECEIPT_KEY_BLOCKER_REF),
        ({"reviewer_notes": "must not be exported"}, cr.P7_R54_AHR_CR09_FORBIDDEN_RECEIPT_KEY_BLOCKER_REF),
        ({"question_text": "must not be exported"}, cr.P7_R54_AHR_CR09_FORBIDDEN_RECEIPT_KEY_BLOCKER_REF),
    ],
)
def test_cr09_blocks_when_receipt_material_is_missing_incomplete_or_unsafe(
    receipt_patch: dict[str, object], expected_blocker: str
) -> None:
    receipt_input = cr.build_p7_r54_ahr_cr09_bodyfree_operation_receipt_input()
    receipt_input.update(receipt_patch)
    material = cr.build_p7_r54_ahr_cr09_actual_local_human_review_operation_receipt(
        reviewer_selection_form=_cr08_ready(),
        operation_receipt_input=receipt_input,
    )

    assert material["operation_receipt_ready"] is False
    assert expected_blocker in material["operation_receipt_blocker_refs"]
    assert material["operation_receipt_ref_present"] is False
    assert material["reviewer_person_ref_matches_cr08"] is False
    assert material["actual_human_review_executed_by_person"] is False
    assert material["actual_human_review_run_here"] is False
    assert material["actual_human_review_operation_run"] is False
    assert material["actual_review_evidence_complete"] is False
    assert material["next_required_step"] == cr.P7_R54_AHR_CR09_DEFAULT_BLOCKED_NEXT_REQUIRED_STEP_REF
    assert cr.assert_p7_r54_ahr_cr09_actual_local_human_review_operation_receipt_contract(material) is True


def test_cr09_blocks_when_cr08_reviewer_form_is_not_ready() -> None:
    material = cr.build_p7_r54_ahr_cr09_actual_local_human_review_operation_receipt(
        reviewer_selection_form=cr.build_p7_r54_ahr_cr08_reviewer_selection_form(packet_generation_receipt_scan=_cr07_ready()),
        operation_receipt_input=cr.build_p7_r54_ahr_cr09_bodyfree_operation_receipt_input(),
    )

    assert material["cr08_reviewer_selection_form_ready"] is False
    assert material["operation_receipt_ready"] is False
    assert cr.P7_R54_AHR_CR09_CR08_NOT_READY_BLOCKER_REF in material["operation_receipt_blocker_refs"]
    assert cr.P7_R54_AHR_CR09_CR08_REVIEWER_PERSON_REF_MISSING_BLOCKER_REF in material["operation_receipt_blocker_refs"]
    assert cr.P7_R54_AHR_CR09_CR08_REVIEWER_PERSON_NOT_CONFIRMED_BLOCKER_REF in material["operation_receipt_blocker_refs"]
    assert material["actual_human_review_run_here"] is False
    assert material["next_required_step"] == cr.P7_R54_AHR_CR09_DEFAULT_BLOCKED_NEXT_REQUIRED_STEP_REF
    assert cr.assert_p7_r54_ahr_cr09_actual_local_human_review_operation_receipt_contract(material) is True


@pytest.mark.parametrize(
    "key,value",
    [
        ("cr08_schema_version", "changed"),
        ("cr08_next_required_step", "not_cr09"),
        ("cr08_reviewer_selection_form_ready", False),
        ("cr08_reviewer_person_ref_present", False),
        ("cr08_reviewer_is_person", False),
        ("cr08_reviewer_person_confirmed", False),
        ("cr08_selection_row_count_required", 23),
        ("cr08_selection_only", False),
        ("cr08_free_text_allowed", True),
        ("cr08_question_text_allowed", True),
        ("operation_receipt_allowed_status_refs", ["changed"]),
        ("operation_receipt_status_ref", cr.P7_R54_AHR_CR09_OPERATION_RECEIPT_BLOCKED_STATUS_REF),
        ("operation_receipt_ready", False),
        ("operation_receipt_reason_refs", []),
        ("operation_receipt_blocker_refs", ["blocked"]),
        ("operation_receipt_blocker_ref_count", 99),
        ("operation_receipt_input_provided", False),
        ("operation_receipt_input_forbidden_key_detected", True),
        ("operation_receipt_ref", ""),
        ("operation_receipt_ref_present", False),
        ("reviewer_person_ref", ""),
        ("reviewer_person_ref_matches_cr08", False),
        ("reviewer_is_person", False),
        ("reviewer_person_confirmed", False),
        ("reviewer_local_only_read_receipt_present", False),
        ("actual_human_review_executed_by_person", False),
        ("review_started_at_bucket_ref", ""),
        ("review_started_at_bucket_ref_present", False),
        ("review_completed_at_bucket_ref", ""),
        ("review_completed_at_bucket_ref_present", False),
        ("reviewed_case_count", 23),
        ("reviewed_case_count_matches_manifest", False),
        ("selection_row_count", 23),
        ("selection_row_count_matches_required", False),
        ("local_only", False),
        ("must_not_export", False),
        ("selection_only", False),
        ("operation_receipt_bodyfree_only", False),
        ("operation_receipt_does_not_include_body", False),
        ("operation_receipt_does_not_include_reviewer_free_text", False),
        ("operation_receipt_does_not_include_question_text", False),
        ("operation_receipt_does_not_include_local_absolute_path", False),
        ("operation_receipt_does_not_include_body_hash", False),
        ("operation_receipt_does_not_include_terminal_output", False),
        ("operation_receipt_does_not_create_rating_rows", False),
        ("operation_receipt_does_not_create_question_rows", False),
        ("operation_receipt_does_not_create_disposal_receipt", False),
        ("actual_human_review_operation_run", False),
        ("actual_human_review_run_here", False),
        ("actual_human_review_complete", True),
        ("actual_review_evidence_complete", True),
        ("actual_rating_rows_materialized_here", True),
        ("actual_question_need_observation_rows_materialized_here", True),
        ("actual_disposal_receipt_materialized_here", True),
        ("disposal_verified", True),
        ("p5_confirmed_final", True),
        ("p6_start_allowed", True),
        ("p8_start_allowed", True),
        ("release_allowed", True),
        ("implemented_steps", []),
        ("not_yet_implemented_steps", []),
        ("next_required_step", "not_cr10"),
    ],
)
def test_cr09_rejects_receipt_mutations_evidence_promotion_or_release_claim(key: str, value: object) -> None:
    mutated = deepcopy(_cr09_ready())
    mutated[key] = value
    with pytest.raises(ValueError):
        cr.assert_p7_r54_ahr_cr09_actual_local_human_review_operation_receipt_contract(mutated)


def test_cr09_rejects_forbidden_body_or_question_key_in_material() -> None:
    mutated = deepcopy(_cr09_ready())
    mutated["reviewer_notes"] = "must not be exported"
    with pytest.raises(ValueError):
        cr.assert_p7_r54_ahr_cr09_actual_local_human_review_operation_receipt_contract(mutated)


def test_cr08_cr09_alias_functions_match_primary_builders_and_contracts() -> None:
    cr08 = cr.build_p7_r54_ahr_current_received_actual_local_review_operation_reviewer_selection_form_bodyfree(
        packet_generation_receipt_scan=_cr07_ready(),
        reviewer_person_ref=cr.P7_R54_AHR_CR08_DEFAULT_REVIEWER_PERSON_REF,
        reviewer_is_person=True,
        reviewer_person_confirmed=True,
    )
    cr09 = cr.build_p7_r54_ahr_current_received_actual_local_review_operation_actual_local_human_review_operation_receipt_bodyfree(
        reviewer_selection_form=cr08,
        operation_receipt_input=cr.build_p7_r54_ahr_cr09_bodyfree_operation_receipt_input(),
    )

    assert cr.assert_p7_r54_ahr_current_received_actual_local_review_operation_reviewer_selection_form_bodyfree_contract(cr08) is True
    assert cr.assert_p7_r54_ahr_current_received_actual_local_review_operation_actual_local_human_review_operation_receipt_bodyfree_contract(cr09) is True
    assert cr08["operation_step_ref"] == cr.P7_R54_AHR_CR08_STEP_REF
    assert cr09["operation_step_ref"] == cr.P7_R54_AHR_CR09_STEP_REF
    assert cr09["next_required_step"] == cr.P7_R54_AHR_CR10_STEP_REF
