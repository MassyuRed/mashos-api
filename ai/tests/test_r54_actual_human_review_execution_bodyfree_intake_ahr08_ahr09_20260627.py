# -*- coding: utf-8 -*-
"""Tests for R54-AHR08/AHR09 body-free packet scan and reviewer form freeze."""

from __future__ import annotations

from copy import deepcopy

import pytest

import emlis_ai_p7_r54_actual_human_review_execution_bodyfree_intake_20260627 as ahr


BODY_FREE_FALSE_FLAGS = (
    "raw_input_included",
    "raw_body_included",
    "returned_emlis_body_included",
    "history_surface_included",
    "body_full_packet_content_included",
    "packet_content_included",
    "reviewer_free_text_included",
    "reviewer_notes_body_included",
    "question_text_included",
    "draft_question_text_included",
    "local_absolute_path_included",
    "body_hash_included",
    "terminal_output_body_included",
)

NO_TOUCH_FALSE_FLAGS = (
    "api_changed",
    "db_changed",
    "rn_changed",
    "runtime_changed",
    "api_route_changed",
    "request_key_changed",
    "response_key_changed",
    "db_schema_changed",
    "db_migration_added",
    "rn_ui_changed",
    "public_response_key_changed",
    "question_implementation_started_here",
    "question_trigger_logic_implemented",
    "question_api_implemented",
    "question_db_schema_implemented",
    "question_rn_ui_implemented",
    "question_answer_persistence_implemented",
    "p8_question_implementation_spec_finalized_here",
    "question_text_materialized_here",
    "draft_question_text_materialized_here",
    "actual_human_review_run_here",
    "actual_human_review_executed_by_person",
    "actual_rating_rows_materialized_here",
    "actual_question_need_observation_rows_materialized_here",
    "actual_disposal_receipt_materialized_here",
    "actual_r52_reintake_execution_confirmed",
    "p5_human_blind_qa_confirmed_final",
    "p6_start_allowed",
    "p8_start_allowed",
    "release_allowed",
)


def assert_bodyfree_no_touch(material: dict[str, object]) -> None:
    assert material["body_free"] is True
    for key in BODY_FREE_FALSE_FLAGS:
        if key in material:
            assert material[key] is False, key
    for key in NO_TOUCH_FALSE_FLAGS:
        if key in material:
            assert material[key] is False, key


def test_r54_ahr08_default_packet_scan_passes_bodyfree_contract() -> None:
    receipt = ahr.build_p7_r54_ahr07_local_packet_generation_operation_receipt_intake()
    material = ahr.build_p7_r54_ahr08_packet_completeness_export_denylist_scan(
        local_packet_generation_receipt=receipt
    )

    assert ahr.assert_p7_r54_ahr08_packet_completeness_export_denylist_scan_contract(material) is True
    assert material["schema_version"] == ahr.P7_R54_AHR08_PACKET_COMPLETENESS_EXPORT_DENYLIST_SCAN_SCHEMA_VERSION
    assert material["operation_step_ref"] == ahr.P7_R54_AHR08_STEP_REF
    assert material["scan_status"] == ahr.P7_R54_AHR08_SCAN_PASSED_STATUS_REF
    assert material["scan_status_ref"] == material["scan_status"]
    assert material["scan_reason_refs"] == [ahr.P7_R54_AHR08_READY_REASON_REF]
    assert material["receipt_ready_for_packet_scan"] is True
    assert material["required_case_count"] == 24
    assert material["expected_packet_count"] == 24
    assert material["scanned_case_count"] == 24
    assert material["scanned_packet_count"] == 24
    assert material["scanned_packet_ref_id_count"] == 24
    assert material["scanned_packet_refs_unique"] is True
    assert material["packet_count_complete"] is True
    assert material["packet_completeness_passed"] is True
    assert material["export_denylist_scan_passed"] is True
    assert material["forbidden_key_scan_passed"] is True
    assert material["forbidden_key_findings_count"] == 0
    assert material["reviewer_selection_form_freeze_allowed_next"] is True
    assert material["actual_review_execution_allowed_next"] is False
    assert material["actual_human_review_run_here"] is False
    assert material["next_required_step"] == ahr.P7_R54_AHR09_STEP_REF
    assert tuple(material["implemented_steps"]) == ahr.P7_R54_AHR08_IMPLEMENTED_STEPS
    assert tuple(material["not_yet_implemented_steps"]) == ahr.P7_R54_AHR08_NOT_YET_IMPLEMENTED_STEPS
    assert_bodyfree_no_touch(material)


@pytest.mark.parametrize(
    "kwargs,expected_blocker",
    [
        ({"scanned_case_count": 23}, "scanned_case_count_not_24"),
        ({"scanned_packet_count": 23}, "scanned_packet_count_not_24"),
        ({"local_only": False}, "local_only_not_confirmed"),
        ({"must_not_export": False}, "must_not_export_not_confirmed"),
        ({"exported": True}, "scan_marked_exported"),
        ({"local_packet_exported": True}, "local_packet_exported"),
        ({"forbidden_key_findings": ["question_text"]}, "forbidden_key_found:question_text"),
    ],
)
def test_r54_ahr08_blocks_incomplete_or_unsafe_scan(kwargs: dict[str, object], expected_blocker: str) -> None:
    material = ahr.build_p7_r54_ahr08_packet_completeness_export_denylist_scan(**kwargs)

    assert ahr.assert_p7_r54_ahr08_packet_completeness_export_denylist_scan_contract(material) is True
    assert material["scan_status"] == ahr.P7_R54_AHR08_SCAN_BLOCKED_STATUS_REF
    assert expected_blocker in material["execution_blocker_ids"]
    assert material["packet_completeness_passed"] is False
    assert material["export_denylist_scan_passed"] is False
    assert material["forbidden_key_scan_passed"] is False
    assert material["reviewer_selection_form_freeze_allowed_next"] is False
    assert material["actual_review_execution_allowed_next"] is False
    assert material["next_required_step"] == ahr.P7_R54_AHR08_BLOCKED_NEXT_REQUIRED_STEP_REF
    assert tuple(material["implemented_steps"]) == ahr.P7_R54_AHR07_IMPLEMENTED_STEPS
    assert_bodyfree_no_touch(material)


def test_r54_ahr08_blocks_when_ahr07_receipt_is_not_ready() -> None:
    blocked_receipt = ahr.build_p7_r54_ahr07_local_packet_generation_operation_receipt_intake(
        generated_packet_count=23
    )
    material = ahr.build_p7_r54_ahr08_packet_completeness_export_denylist_scan(
        local_packet_generation_receipt=blocked_receipt
    )

    assert material["scan_status"] == ahr.P7_R54_AHR08_SCAN_BLOCKED_STATUS_REF
    assert "ahr07_packet_generation_receipt_not_ready" in material["execution_blocker_ids"]
    assert "ahr07_packet_scan_not_allowed_next" in material["execution_blocker_ids"]
    assert ahr.assert_p7_r54_ahr08_packet_completeness_export_denylist_scan_contract(material) is True


@pytest.mark.parametrize(
    "field,bad_value",
    [
        ("raw_input_included", True),
        ("returned_emlis_body_included", True),
        ("history_surface_included", True),
        ("question_text_included", True),
        ("draft_question_text_included", True),
        ("local_absolute_path_included", True),
        ("body_hash_included", True),
        ("packet_content_included", True),
        ("actual_human_review_run_here", True),
        ("actual_review_execution_allowed_next", True),
    ],
)
def test_r54_ahr08_rejects_body_leak_question_leak_or_premature_review_mutations(field: str, bad_value: object) -> None:
    material = ahr.build_p7_r54_ahr08_packet_completeness_export_denylist_scan()
    mutated = deepcopy(material)
    mutated[field] = bad_value

    with pytest.raises(ValueError):
        ahr.assert_p7_r54_ahr08_packet_completeness_export_denylist_scan_contract(mutated)


def test_r54_ahr09_default_selection_form_freezes_after_passed_scan() -> None:
    scan = ahr.build_p7_r54_ahr08_packet_completeness_export_denylist_scan()
    material = ahr.build_p7_r54_ahr09_reviewer_selection_form_freeze(packet_completeness_scan=scan)

    assert ahr.assert_p7_r54_ahr09_reviewer_selection_form_freeze_contract(material) is True
    assert material["schema_version"] == ahr.P7_R54_AHR09_REVIEWER_SELECTION_FORM_FREEZE_SCHEMA_VERSION
    assert material["operation_step_ref"] == ahr.P7_R54_AHR09_STEP_REF
    assert material["selection_form_status"] == ahr.P7_R54_AHR09_FORM_FROZEN_STATUS_REF
    assert material["selection_form_status_ref"] == material["selection_form_status"]
    assert material["packet_scan_ready_for_form_freeze"] is True
    assert material["selection_only"] is True
    assert material["selection_only_form"] is True
    assert material["selection_form_structure_frozen"] is True
    assert material["selection_form_bodyfree_only"] is True
    assert material["actual_human_review_local_only_operation_allowed_next"] is True
    assert material["actual_review_execution_allowed_here"] is False
    assert material["actual_review_execution_allowed_next"] is False
    assert material["actual_human_review_run_here"] is False
    assert material["next_required_step"] == ahr.P7_R54_AHR10_STEP_REF
    assert tuple(material["implemented_steps"]) == ahr.P7_R54_AHR09_IMPLEMENTED_STEPS
    assert tuple(material["not_yet_implemented_steps"]) == ahr.P7_R54_AHR09_NOT_YET_IMPLEMENTED_STEPS
    assert_bodyfree_no_touch(material)


def test_r54_ahr09_freezes_all_required_selection_options_without_text_fields() -> None:
    material = ahr.build_p7_r54_ahr09_reviewer_selection_form_freeze()

    assert tuple(material["rating_axis_refs"]) == ahr.P7_R54_AHR05_RATING_AXIS_REFS
    assert material["rating_axis_target_thresholds"] == ahr.P7_R54_AHR05_RATING_AXIS_TARGET_THRESHOLDS
    assert tuple(material["score_option_refs"]) == ahr.P7_R54_AHR09_SCORE_OPTION_REFS
    assert tuple(material["verdict_option_refs"]) == ahr.P7_R54_AHR09_VERDICT_OPTION_REFS
    assert tuple(material["sanitized_reason_id_option_refs"]) == ahr.P7_R54_AHR09_SANITIZED_REASON_ID_OPTION_REFS
    assert tuple(material["readfeel_blocker_id_option_refs"]) == ahr.P7_R54_AHR09_READFEEL_BLOCKER_ID_OPTION_REFS
    assert tuple(material["execution_blocker_id_option_refs"]) == ahr.P7_R54_AHR09_EXECUTION_BLOCKER_ID_OPTION_REFS
    assert tuple(material["question_need_primary_class_options"]) == ahr.P7_R54_AHR09_QUESTION_NEED_PRIMARY_CLASS_REFS
    assert tuple(material["ambiguity_kind_option_refs"]) == ahr.P7_R54_AHR09_AMBIGUITY_KIND_OPTION_REFS
    assert tuple(material["one_question_fit_option_refs"]) == ahr.P7_R54_AHR09_ONE_QUESTION_FIT_OPTION_REFS
    assert tuple(material["repair_required_option_refs"]) == ahr.P7_R54_AHR09_REPAIR_REQUIRED_OPTION_REFS
    assert tuple(material["plan_candidate_flag_refs"]) == ahr.P7_R54_AHR09_PLAN_CANDIDATE_FLAG_REFS
    assert material["free_text_export_allowed"] is False
    assert material["reviewer_free_text_field_present"] is False
    assert material["question_text_input_allowed"] is False
    assert material["draft_question_text_input_allowed"] is False
    assert material["raw_body_copy_field_present"] is False
    assert material["history_surface_copy_field_present"] is False


@pytest.mark.parametrize(
    "kwargs,expected_blocker",
    [
        ({"selection_only": False}, "selection_only_not_confirmed"),
        ({"free_text_export_allowed": True}, "free_text_export_allowed"),
        ({"reviewer_free_text_field_present": True}, "reviewer_free_text_field_present"),
        ({"question_text_input_allowed": True}, "question_text_input_allowed"),
        ({"draft_question_text_input_allowed": True}, "draft_question_text_input_allowed"),
        ({"raw_body_copy_field_present": True}, "raw_body_copy_field_present"),
        ({"history_surface_copy_field_present": True}, "history_surface_copy_field_present"),
        ({"local_path_field_present": True}, "local_path_field_present"),
        ({"body_hash_field_present": True}, "body_hash_field_present"),
        ({"packet_content_copy_field_present": True}, "packet_content_copy_field_present"),
    ],
)
def test_r54_ahr09_blocks_unsafe_or_non_selection_form(kwargs: dict[str, object], expected_blocker: str) -> None:
    material = ahr.build_p7_r54_ahr09_reviewer_selection_form_freeze(**kwargs)

    assert ahr.assert_p7_r54_ahr09_reviewer_selection_form_freeze_contract(material) is True
    assert material["selection_form_status"] == ahr.P7_R54_AHR09_FORM_BLOCKED_STATUS_REF
    assert expected_blocker in material["execution_blocker_ids"]
    assert material["selection_only_form"] is False
    assert material["selection_form_structure_frozen"] is False
    assert material["selection_form_bodyfree_only"] is False
    assert material["actual_human_review_local_only_operation_allowed_next"] is False
    assert material["actual_human_review_run_here"] is False
    assert material["next_required_step"] == ahr.P7_R54_AHR09_BLOCKED_NEXT_REQUIRED_STEP_REF
    assert_bodyfree_no_touch(material)


def test_r54_ahr09_blocks_when_ahr08_scan_is_blocked() -> None:
    blocked_scan = ahr.build_p7_r54_ahr08_packet_completeness_export_denylist_scan(
        scanned_packet_count=23
    )
    material = ahr.build_p7_r54_ahr09_reviewer_selection_form_freeze(packet_completeness_scan=blocked_scan)

    assert material["selection_form_status"] == ahr.P7_R54_AHR09_FORM_BLOCKED_STATUS_REF
    assert "ahr08_packet_completeness_scan_not_passed" in material["execution_blocker_ids"]
    assert material["packet_scan_ready_for_form_freeze"] is False
    assert ahr.assert_p7_r54_ahr09_reviewer_selection_form_freeze_contract(material) is True


@pytest.mark.parametrize(
    "field,bad_value",
    [
        ("free_text_export_allowed", True),
        ("reviewer_free_text_field_present", True),
        ("question_text_input_allowed", True),
        ("draft_question_text_input_allowed", True),
        ("raw_body_copy_field_present", True),
        ("history_surface_copy_field_present", True),
        ("body_full_packet_content_included", True),
        ("question_text_included", True),
        ("draft_question_text_included", True),
        ("actual_review_execution_allowed_next", True),
        ("actual_human_review_run_here", True),
        ("p8_implementation_spec_finalized_here", True),
    ],
)
def test_r54_ahr09_rejects_body_leak_question_leak_or_premature_review_mutations(field: str, bad_value: object) -> None:
    material = ahr.build_p7_r54_ahr09_reviewer_selection_form_freeze()
    mutated = deepcopy(material)
    mutated[field] = bad_value

    with pytest.raises(ValueError):
        ahr.assert_p7_r54_ahr09_reviewer_selection_form_freeze_contract(mutated)


@pytest.mark.parametrize(
    "field,bad_value",
    [
        ("rating_axis_refs", ["history_connection_naturalness"]),
        ("score_option_refs", [0.0, 1.0]),
        ("verdict_option_refs", ["PASS"]),
        ("question_need_primary_class_options", ["no_question_needed_emlis_can_observe"]),
        ("plan_candidate_flag_refs", ["p8_implementation_spec_finalized_here"]),
    ],
)
def test_r54_ahr09_rejects_selection_option_mutations(field: str, bad_value: object) -> None:
    material = ahr.build_p7_r54_ahr09_reviewer_selection_form_freeze()
    mutated = deepcopy(material)
    mutated[field] = bad_value

    with pytest.raises(ValueError):
        ahr.assert_p7_r54_ahr09_reviewer_selection_form_freeze_contract(mutated)


def test_r54_ahr08_ahr09_design_aliases_point_to_canonical_helpers() -> None:
    scan = ahr.build_p7_r54_actual_human_review_execution_bodyfree_intake_ahr08_packet_completeness_export_denylist_scan()
    form = ahr.build_p7_r54_actual_human_review_execution_bodyfree_intake_ahr09_reviewer_selection_form_freeze(
        packet_completeness_scan=scan
    )

    assert scan == ahr.build_p7_r54_ahr08_packet_completeness_export_denylist_scan()
    assert form["selection_form_status"] == ahr.P7_R54_AHR09_FORM_FROZEN_STATUS_REF
    assert ahr.assert_p7_r54_actual_human_review_execution_bodyfree_intake_ahr08_packet_completeness_export_denylist_scan_contract(scan) is True
    assert ahr.assert_p7_r54_actual_human_review_execution_bodyfree_intake_ahr09_reviewer_selection_form_freeze_contract(form) is True
