# -*- coding: utf-8 -*-
"""R54 current snapshot local review run CLR08-CLR09 contract tests."""

from __future__ import annotations

from copy import deepcopy
from typing import Any

import pytest

import emlis_ai_p7_r54_current_snapshot_local_review_run_20260627 as clr03
import emlis_ai_p7_r54_current_snapshot_local_review_run_clr06_clr07_20260627 as clr07
import emlis_ai_p7_r54_current_snapshot_local_review_run_clr08_clr09_20260627 as clr


FORBIDDEN_BODY_OR_QUESTION_KEYS = (
    "raw_input",
    "returned_emlis_body",
    "history_surface",
    "reviewer_free_text",
    "reviewer_note",
    "reviewer_notes",
    "question_text",
    "draft_question_text",
    "local_path",
    "local_absolute_path",
    "body_hash",
    "packet_content",
    "terminal_output_body",
)


def _assert_bodyfree_no_touch(material: dict[str, Any]) -> None:
    assert material["body_free"] is True
    for key in clr03.P7_R54_CLR_FALSE_FLAG_REFS:
        assert material[key] is False, key
    assert all(value is False for value in material["public_contract"].values())
    assert all(value is False for value in material["r54_clr_no_touch_contract"].values())
    assert all(value is False for value in material["body_free_markers"].values())
    for forbidden_key in FORBIDDEN_BODY_OR_QUESTION_KEYS:
        assert forbidden_key not in material


def _ready_clr07() -> dict[str, Any]:
    request = clr07.build_p7_r54_clr06_body_full_packet_generation_request_bodyfree_evidence()
    receipt = clr07.build_p7_r54_clr07_bodyfree_generated_receipt_from_request(request)
    material = clr07.build_p7_r54_clr07_local_packet_generation_operation_receipt_intake(
        body_full_packet_generation_request_bodyfree_evidence=request,
        packet_generation_operation_receipt=receipt,
    )
    assert clr07.assert_p7_r54_clr07_local_packet_generation_operation_receipt_intake_contract(material) is True
    return material


def _blocked_clr07() -> dict[str, Any]:
    request = clr07.build_p7_r54_clr06_body_full_packet_generation_request_bodyfree_evidence()
    material = clr07.build_p7_r54_clr07_local_packet_generation_operation_receipt_intake(
        body_full_packet_generation_request_bodyfree_evidence=request,
        packet_generation_operation_receipt=None,
    )
    assert clr07.assert_p7_r54_clr07_local_packet_generation_operation_receipt_intake_contract(material) is True
    return material


def _ready_clr08() -> dict[str, Any]:
    material = clr.build_p7_r54_clr08_packet_completeness_export_denylist_scan(
        local_packet_generation_operation_receipt_intake=_ready_clr07()
    )
    assert clr.assert_p7_r54_clr08_packet_completeness_export_denylist_scan_contract(material) is True
    return material


def test_r54_clr00_to_clr07_are_present_before_clr08_clr09() -> None:
    receipt = _ready_clr07()

    assert tuple(receipt["implemented_steps"]) == clr07.P7_R54_CLR07_IMPLEMENTED_STEPS
    assert receipt["packet_generation_status"] == clr07.P7_R54_CLR07_LOCAL_ONLY_PACKET_GENERATED_STATUS_REF
    assert receipt["packet_ref_count"] == 24
    assert receipt["packet_completeness_export_denylist_scan_allowed_next"] is True
    assert receipt["body_full_packet_content_included"] is False
    assert receipt["actual_human_review_run_here"] is False
    assert receipt["next_required_step"] == clr.P7_R54_CLR08_STEP_REF


def test_r54_clr08_packet_completeness_export_denylist_scan_ready_bodyfree() -> None:
    material = _ready_clr08()

    assert set(material) == set(clr.P7_R54_CLR08_PACKET_COMPLETENESS_EXPORT_DENYLIST_SCAN_REQUIRED_FIELD_REFS)
    assert material["schema_version"] == clr.P7_R54_CLR08_PACKET_COMPLETENESS_EXPORT_DENYLIST_SCAN_SCHEMA_VERSION
    assert material["policy_section"] == clr.P7_R54_CLR08_STEP_REF
    assert material["operation_step_ref"] == clr.P7_R54_CLR08_STEP_REF
    assert material["clr07_packet_generation_status"] == clr07.P7_R54_CLR07_LOCAL_ONLY_PACKET_GENERATED_STATUS_REF
    assert material["clr07_receipt_ready"] is True
    assert material["existing_op08_current_refs_are_historical_here"] is True
    assert material["existing_op08_reused_as_actual_packet_scan_basis"] is False
    assert material["existing_op08_structural_contract_reused"] is True

    assert material["packet_scan_status"] == clr.P7_R54_CLR08_PACKET_SCAN_READY_STATUS_REF
    assert material["packet_scan_ref"] == clr.P7_R54_CLR08_PACKET_SCAN_REF
    assert material["packet_scan_reason_refs"] == [clr.P7_R54_CLR08_READY_REASON_REF]
    assert material["execution_blocker_ids"] == []
    assert material["open_execution_blocker_ids"] == []
    assert material["expected_packet_ref_count"] == 24
    assert material["declared_packet_ref_count"] == 24
    assert material["declared_packet_ref_ids_unique"] is True
    assert material["packet_ref_ids_match_receipt_and_request"] is True
    assert material["packet_scan_row_count"] == 24
    assert material["packet_present_count"] == 24
    assert material["required_fields_present_count"] == 24
    assert material["packet_completeness_ready"] is True
    assert material["export_denylist_violation_count"] == 0
    assert material["body_full_packet_export_candidate_count"] == 0
    assert material["reviewer_selection_form_freeze_allowed_next"] is True
    assert material["actual_review_execution_blocked_until_reviewer_selection_form"] is True
    assert material["p5_actual_review_still_not_run"] is True
    assert material["rating_row_count"] == 0
    assert material["question_observation_row_count"] == 0
    assert material["disposal_verified"] is False
    assert tuple(material["implemented_steps"]) == clr.P7_R54_CLR08_IMPLEMENTED_STEPS
    assert tuple(material["not_yet_implemented_steps"]) == clr.P7_R54_CLR08_NOT_YET_IMPLEMENTED_STEPS
    assert material["next_required_step"] == clr.P7_R54_CLR09_STEP_REF

    for row in material["packet_scan_rows"]:
        assert set(row) == set(clr.P7_R54_CLR08_PACKET_SCAN_ROW_REQUIRED_FIELD_REFS)
        assert row["packet_present_local_only"] is True
        assert row["required_fields_present"] is True
        assert row["export_denylist_violation"] is False
        assert row["body_full_packet_export_candidate"] is False
        assert row["body_free"] is True
        for false_key in (
            "packet_content_included",
            "local_path_included",
            "local_absolute_path_included",
            "body_hash_included",
            "raw_body_included",
            "returned_emlis_body_included",
            "history_surface_included",
            "reviewer_free_text_included",
            "question_text_included",
            "draft_question_text_included",
            "terminal_output_body_included",
        ):
            assert row[false_key] is False
        for forbidden_key in FORBIDDEN_BODY_OR_QUESTION_KEYS:
            assert forbidden_key not in row

    for false_key in (
        "packet_scan_contains_packet_content",
        "packet_scan_contains_local_path",
        "packet_scan_contains_local_absolute_path",
        "packet_scan_contains_body_hash",
        "packet_scan_contains_raw_body",
        "packet_scan_contains_returned_body",
        "packet_scan_contains_history_surface",
        "packet_scan_contains_reviewer_free_text",
        "packet_scan_contains_question_text",
        "packet_scan_contains_draft_question_text",
        "packet_scan_contains_terminal_output_body",
        "body_full_packet_content_included",
        "body_full_packet_generated_here",
        "actual_body_full_packet_generated_here",
        "local_review_root_path_included",
        "local_packet_directory_path_included",
        "local_packet_exported",
        "body_full_packet_export_allowed",
        "body_full_packet_zip_inclusion_allowed",
        "reviewer_notes_export_allowed",
        "actual_review_evidence_complete",
        "actual_human_review_run_here",
    ):
        assert material[false_key] is False
    _assert_bodyfree_no_touch(material)


def test_r54_clr08_blocks_when_clr07_receipt_is_not_ready() -> None:
    material = clr.build_p7_r54_clr08_packet_completeness_export_denylist_scan(
        local_packet_generation_operation_receipt_intake=_blocked_clr07()
    )

    assert material["packet_scan_status"] == clr.P7_R54_CLR08_PACKET_SCAN_BLOCKED_STATUS_REF
    assert "r54_clr08_blocked_until_clr07_bodyfree_packet_generation_receipt_ready" in material["execution_blocker_ids"]
    assert material["packet_scan_row_count"] == 0
    assert material["reviewer_selection_form_freeze_allowed_next"] is False
    assert material["next_required_step"] == clr.P7_R54_CLR08_BLOCKED_NEXT_REQUIRED_STEP_REF
    _assert_bodyfree_no_touch(material)
    assert clr.assert_p7_r54_clr08_packet_completeness_export_denylist_scan_contract(material) is True


def test_r54_clr08_blocks_incomplete_packet_rows_bodyfree() -> None:
    receipt = _ready_clr07()
    rows = deepcopy(_ready_clr08()["packet_scan_rows"])
    rows[0]["required_fields_present"] = False

    material = clr.build_p7_r54_clr08_packet_completeness_export_denylist_scan(
        local_packet_generation_operation_receipt_intake=receipt,
        packet_scan_rows=rows,
    )

    assert material["packet_scan_status"] == clr.P7_R54_CLR08_PACKET_SCAN_BLOCKED_INCOMPLETE_STATUS_REF
    assert "packet_required_fields_missing" in material["execution_blocker_ids"]
    assert material["required_fields_present_count"] == 23
    assert material["reviewer_selection_form_freeze_allowed_next"] is False
    _assert_bodyfree_no_touch(material)
    assert clr.assert_p7_r54_clr08_packet_completeness_export_denylist_scan_contract(material) is True


@pytest.mark.parametrize(
    "kwargs,expected_status,expected_blocker",
    [
        (
            {"export_denylist_violation_refs": ["p7r48-p5-packet-r54clr-001"]},
            clr.P7_R54_CLR08_PACKET_SCAN_BLOCKED_BY_LEAK_STATUS_REF,
            "export_denylist_violation_detected",
        ),
        (
            {"body_full_packet_export_candidate_refs": ["p7r48-p5-packet-r54clr-001"]},
            clr.P7_R54_CLR08_PACKET_SCAN_BLOCKED_BY_LEAK_STATUS_REF,
            "body_full_packet_export_candidate_detected",
        ),
        (
            {"body_full_packet_content_detected_in_export": True},
            clr.P7_R54_CLR08_PACKET_SCAN_BLOCKED_BY_LEAK_STATUS_REF,
            "body_full_packet_content_detected_in_export",
        ),
        (
            {"question_text_detected_in_export": True},
            clr.P7_R54_CLR08_PACKET_SCAN_BLOCKED_BY_LEAK_STATUS_REF,
            "question_text_detected_in_export",
        ),
        (
            {"local_path_detected_in_export": True},
            clr.P7_R54_CLR08_PACKET_SCAN_BLOCKED_BY_LEAK_STATUS_REF,
            "local_path_detected_in_export",
        ),
    ],
)
def test_r54_clr08_blocks_export_denylist_or_leak_boundary(kwargs: dict[str, object], expected_status: str, expected_blocker: str) -> None:
    material = clr.build_p7_r54_clr08_packet_completeness_export_denylist_scan(
        local_packet_generation_operation_receipt_intake=_ready_clr07(),
        **kwargs,
    )

    assert material["packet_scan_status"] == expected_status
    assert expected_blocker in material["execution_blocker_ids"]
    assert material["reviewer_selection_form_freeze_allowed_next"] is False
    _assert_bodyfree_no_touch(material)
    assert clr.assert_p7_r54_clr08_packet_completeness_export_denylist_scan_contract(material) is True


def test_r54_clr09_reviewer_selection_form_freeze_ready_bodyfree() -> None:
    scan = _ready_clr08()
    material = clr.build_p7_r54_clr09_reviewer_selection_form_freeze(packet_completeness_export_denylist_scan=scan)

    assert set(material) == set(clr.P7_R54_CLR09_REVIEWER_SELECTION_FORM_FREEZE_REQUIRED_FIELD_REFS)
    assert material["schema_version"] == clr.P7_R54_CLR09_REVIEWER_SELECTION_FORM_FREEZE_SCHEMA_VERSION
    assert material["policy_section"] == clr.P7_R54_CLR09_STEP_REF
    assert material["operation_step_ref"] == clr.P7_R54_CLR09_STEP_REF
    assert material["clr08_packet_scan_ready"] is True
    assert material["existing_op09_current_refs_are_historical_here"] is True
    assert material["existing_op09_reused_as_actual_form_basis"] is False
    assert material["existing_op09_structural_contract_reused"] is True

    assert material["reviewer_selection_form_status"] == clr.P7_R54_CLR09_FORM_READY_STATUS_REF
    assert material["reviewer_selection_form_ref"] == clr.P7_R54_CLR09_REVIEWER_SELECTION_FORM_REF
    assert material["reviewer_selection_form_policy_ref"] == clr.P7_R54_CLR09_REVIEWER_SELECTION_FORM_POLICY_REF
    assert material["rating_form_ref"] == clr.P7_R54_CLR09_RATING_FORM_REF
    assert material["reviewer_selection_form_reason_refs"] == [clr.P7_R54_CLR09_READY_REASON_REF]
    assert material["execution_blocker_ids"] == []
    assert material["selection_only_form"] is True
    assert material["reviewer_selection_form_materialized_here"] is True
    assert material["rating_form_materialized_here"] is True
    assert tuple(material["rating_axis_refs"]) == clr.P7_R54_CLR09_RATING_AXIS_REFS
    assert "overall_read_feeling_ref" not in material["rating_axis_refs"]
    assert material["rating_axis_count"] == 6
    assert tuple(material["score_option_refs"]) == clr.P7_R54_CLR09_SCORE_OPTION_REFS
    assert tuple(material["verdict_option_refs"]) == clr.P7_R54_CLR09_VERDICT_OPTION_REFS
    assert "NOT_REVIEWABLE" in material["verdict_option_refs"]
    assert tuple(material["overall_read_feeling_option_refs"]) == clr.P7_R54_CLR09_OVERALL_READ_FEELING_OPTION_REFS
    assert tuple(material["question_need_primary_class_options"]) == clr.P7_R54_CLR09_QUESTION_NEED_PRIMARY_CLASS_REFS

    for false_key in (
        "reviewer_free_text_field_present",
        "reviewer_free_text_export_allowed",
        "raw_body_copy_field_present",
        "question_text_field_present",
        "draft_question_text_field_present",
        "local_path_field_present",
        "local_absolute_path_field_present",
        "body_hash_field_present",
        "packet_content_field_present",
        "terminal_output_body_field_present",
        "rating_form_contains_question_text",
        "rating_form_contains_raw_body_copy",
        "rating_form_contains_local_path",
        "rating_form_contains_local_absolute_path",
        "rating_form_contains_body_hash",
        "rating_form_contains_packet_content",
        "rating_form_contains_terminal_output_body",
        "rating_form_contains_reviewer_free_text_export",
        "actual_human_review_started_here",
        "actual_human_review_run_here",
        "actual_review_evidence_complete",
        "disposal_verified_before_form",
        "disposal_verified_before_review",
    ):
        assert material[false_key] is False
    assert material["p5_actual_review_still_not_run"] is True
    assert material["rating_row_count"] == 0
    assert material["question_observation_row_count"] == 0
    assert material["disposal_verified"] is False
    assert tuple(material["implemented_steps"]) == clr.P7_R54_CLR09_IMPLEMENTED_STEPS
    assert tuple(material["not_yet_implemented_steps"]) == clr.P7_R54_CLR09_NOT_YET_IMPLEMENTED_STEPS
    assert material["next_required_step"] == clr.P7_R54_CLR10_STEP_REF
    _assert_bodyfree_no_touch(material)
    assert clr.assert_p7_r54_clr09_reviewer_selection_form_freeze_contract(material) is True


def test_r54_clr09_blocks_when_clr08_scan_is_not_ready() -> None:
    scan = clr.build_p7_r54_clr08_packet_completeness_export_denylist_scan(
        local_packet_generation_operation_receipt_intake=_ready_clr07(),
        question_text_detected_in_export=True,
    )
    form = clr.build_p7_r54_clr09_reviewer_selection_form_freeze(packet_completeness_export_denylist_scan=scan)

    assert form["reviewer_selection_form_status"] == clr.P7_R54_CLR09_FORM_BLOCKED_STATUS_REF
    assert "r54_clr09_blocked_until_clr08_packet_scan_ready" in form["execution_blocker_ids"]
    assert form["selection_only_form"] is False
    assert form["rating_axis_refs"] == []
    assert form["score_option_refs"] == []
    assert form["verdict_option_refs"] == []
    assert form["overall_read_feeling_option_refs"] == []
    assert form["question_need_primary_class_options"] == []
    assert form["actual_human_review_run_here"] is False
    assert form["next_required_step"] == clr.P7_R54_CLR09_BLOCKED_NEXT_REQUIRED_STEP_REF
    _assert_bodyfree_no_touch(form)
    assert clr.assert_p7_r54_clr09_reviewer_selection_form_freeze_contract(form) is True


@pytest.mark.parametrize(
    "builder,asserter,key,value",
    [
        (clr.build_p7_r54_clr08_packet_completeness_export_denylist_scan, clr.assert_p7_r54_clr08_packet_completeness_export_denylist_scan_contract, "packet_scan_contains_packet_content", True),
        (clr.build_p7_r54_clr08_packet_completeness_export_denylist_scan, clr.assert_p7_r54_clr08_packet_completeness_export_denylist_scan_contract, "body_full_packet_generated_here", True),
        (clr.build_p7_r54_clr08_packet_completeness_export_denylist_scan, clr.assert_p7_r54_clr08_packet_completeness_export_denylist_scan_contract, "p8_start_allowed", True),
        (clr.build_p7_r54_clr09_reviewer_selection_form_freeze, clr.assert_p7_r54_clr09_reviewer_selection_form_freeze_contract, "reviewer_free_text_field_present", True),
        (clr.build_p7_r54_clr09_reviewer_selection_form_freeze, clr.assert_p7_r54_clr09_reviewer_selection_form_freeze_contract, "actual_human_review_run_here", True),
        (clr.build_p7_r54_clr09_reviewer_selection_form_freeze, clr.assert_p7_r54_clr09_reviewer_selection_form_freeze_contract, "release_allowed", True),
    ],
)
def test_r54_clr08_clr09_reject_bodyfull_question_review_or_promotion_mutations(
    builder: Any, asserter: Any, key: str, value: object
) -> None:
    material = builder()
    mutated = deepcopy(material)
    mutated[key] = value
    with pytest.raises((ValueError, AssertionError)):
        asserter(mutated)


def test_r54_clr08_clr09_reject_forbidden_payload_or_question_keys() -> None:
    scan = _ready_clr08()
    mutated_scan = deepcopy(scan)
    mutated_scan["packet_content"] = "forbidden"
    with pytest.raises((ValueError, AssertionError)):
        clr.assert_p7_r54_clr08_packet_completeness_export_denylist_scan_contract(mutated_scan)

    form = clr.build_p7_r54_clr09_reviewer_selection_form_freeze(packet_completeness_export_denylist_scan=scan)
    mutated_form = deepcopy(form)
    mutated_form["question_text"] = "forbidden"
    with pytest.raises((ValueError, AssertionError)):
        clr.assert_p7_r54_clr09_reviewer_selection_form_freeze_contract(mutated_form)


def test_r54_clr08_clr09_aliases_remain_available() -> None:
    scan = clr.build_p7_r54_current_snapshot_local_run_clr08_packet_completeness_export_denylist_scan()
    assert clr.assert_p7_r54_current_snapshot_local_run_clr08_packet_completeness_export_denylist_scan_contract(scan) is True
    assert clr.assert_p7_r54_current_snapshot_packet_completeness_export_denylist_scan_bodyfree_contract(scan) is True

    form = clr.build_p7_r54_current_snapshot_local_run_clr09_reviewer_selection_form_freeze(
        packet_completeness_export_denylist_scan=scan
    )
    assert clr.assert_p7_r54_current_snapshot_local_run_clr09_reviewer_selection_form_freeze_contract(form) is True
    assert clr.assert_p7_r54_current_snapshot_reviewer_selection_form_freeze_bodyfree_contract(form) is True
