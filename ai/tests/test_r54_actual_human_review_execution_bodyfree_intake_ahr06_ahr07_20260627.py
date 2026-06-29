# -*- coding: utf-8 -*-
"""Tests for R54-AHR06/AHR07 body-free packet request and receipt boundaries."""

from __future__ import annotations

from copy import deepcopy

import pytest

import emlis_ai_p7_r54_actual_human_review_execution_bodyfree_intake_20260627 as ahr


FORBIDDEN_BODY_OR_QUESTION_REFS = (
    "raw_input_included",
    "raw_body_included",
    "returned_emlis_body_included",
    "history_surface_included",
    "reviewer_free_text_included",
    "reviewer_notes_body_included",
    "question_text_included",
    "draft_question_text_included",
    "local_absolute_path_included",
    "body_hash_included",
    "packet_content_included",
    "terminal_output_body_included",
)

NO_TOUCH_FALSE_REFS = (
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
    "body_full_packet_generation_started_here",
    "body_full_packet_generation_requested_here",
    "body_full_packet_generated_here",
    "actual_human_review_run_here",
    "actual_human_review_executed_by_person",
    "actual_rating_rows_materialized_here",
    "actual_question_need_observation_rows_materialized_here",
    "actual_disposal_receipt_materialized_here",
    "actual_r52_reintake_execution_confirmed",
    "p5_human_blind_qa_confirmed_candidate",
    "p5_human_blind_qa_confirmed_final",
    "p6_start_allowed",
    "p8_start_allowed",
    "p7_complete",
    "release_allowed",
)


def _assert_bodyfree_no_touch(material: dict[str, object]) -> None:
    assert material["body_free"] is True
    for key in FORBIDDEN_BODY_OR_QUESTION_REFS:
        assert material[key] is False
    for key in NO_TOUCH_FALSE_REFS:
        assert material[key] is False
    assert all(value is False for value in material["public_contract"].values())
    assert all(value is False for value in material["r54_ahr_no_touch_contract"].values())
    assert all(value is False for value in material["body_free_markers"].values())


def test_r54_ahr06_records_body_full_packet_generation_request_as_bodyfree_evidence_only() -> None:
    material = ahr.build_p7_r54_ahr06_body_full_packet_generation_request_bodyfree_evidence()

    assert set(material) == set(ahr.P7_R54_AHR06_BODY_FULL_PACKET_GENERATION_REQUEST_REQUIRED_FIELD_REFS)
    assert material["schema_version"] == ahr.P7_R54_AHR06_BODY_FULL_PACKET_GENERATION_REQUEST_BODYFREE_EVIDENCE_SCHEMA_VERSION
    assert material["policy_section"] == ahr.P7_R54_AHR06_STEP_REF
    assert material["operation_step_ref"] == ahr.P7_R54_AHR06_STEP_REF
    assert material["ahr05_schema_version"] == ahr.P7_R54_AHR_24_CASE_MANIFEST_FREEZE_SCHEMA_VERSION
    assert material["ahr05_manifest_status"] == ahr.P7_R54_AHR05_MANIFEST_READY_STATUS_REF
    assert material["ahr05_body_full_packet_generation_request_allowed_next"] is True
    assert material["ahr05_case_rows_bodyfree_only"] is True

    assert material["packet_generation_request_status"] == ahr.P7_R54_AHR06_REQUEST_READY_STATUS_REF
    assert material["packet_generation_request_reason_refs"] == [ahr.P7_R54_AHR06_READY_REASON_REF]
    assert material["execution_blocker_ids"] == []
    assert material["manifest_ready_for_packet_generation_request"] is True
    assert material["body_full_packet_generation_request_allowed_from_manifest"] is True
    assert material["local_only"] is True
    assert material["must_not_export"] is True
    assert material["disposal_required"] is True
    assert material["explicit_allow_token_present"] is True
    assert material["packet_generation_request_ref"] == ahr.P7_R54_AHR06_EXPLICIT_REQUEST_REF
    assert material["packet_generation_request_ref_present"] is True
    assert material["packet_generation_request_is_ref_only"] is True
    assert material["local_packet_generation_operation_ref"] == ahr.P7_R54_AHR06_LOCAL_PACKET_GENERATION_OPERATION_REF
    assert material["local_packet_generation_operation_ref_only"] is True

    assert material["required_case_count"] == 24
    assert material["case_row_count"] == 24
    assert material["case_ref_id_count"] == 24
    assert material["blind_case_id_count"] == 24
    assert material["packet_ref_id_count"] == 24
    assert material["packet_ref_ids_unique"] is True
    assert material["packet_generation_requested"] is True
    assert material["packet_generation_requested_as_bodyfree_evidence_only"] is True
    assert material["body_full_packet_generation_request_evidence_only"] is True
    assert material["body_full_packet_generation_requested_here"] is False
    assert material["body_full_generation_requested_here"] is False
    assert material["body_full_packet_generated_here"] is False
    assert material["body_full_packet_content_included"] is False
    assert material["local_packet_generation_operation_allowed_next"] is True
    assert material["local_packet_generation_receipt_required_next"] is True
    assert material["actual_review_execution_blocked_until_local_packet_receipt"] is True
    assert tuple(material["implemented_steps"]) == ahr.P7_R54_AHR06_IMPLEMENTED_STEPS
    assert tuple(material["not_yet_implemented_steps"]) == ahr.P7_R54_AHR06_NOT_YET_IMPLEMENTED_STEPS
    assert material["next_required_step"] == ahr.P7_R54_AHR07_STEP_REF
    _assert_bodyfree_no_touch(material)
    assert ahr.assert_p7_r54_ahr06_body_full_packet_generation_request_bodyfree_evidence_contract(material) is True


@pytest.mark.parametrize(
    "kwargs,expected_blocker",
    [
        ({"packet_generation_request_ref": "missing"}, "packet_generation_request_ref_missing_or_unexpected"),
        ({"local_packet_generation_operation_ref": "missing"}, "local_packet_generation_operation_ref_missing_or_unexpected"),
        ({"explicit_allow_token_ref": "missing"}, "explicit_allow_token_missing"),
        ({"local_only": False}, "local_only_not_confirmed"),
        ({"must_not_export": False}, "must_not_export_not_confirmed"),
        ({"disposal_required": False}, "disposal_required_not_confirmed"),
    ],
)
def test_r54_ahr06_blocks_when_request_evidence_is_not_safe(kwargs: dict[str, object], expected_blocker: str) -> None:
    material = ahr.build_p7_r54_ahr06_body_full_packet_generation_request_bodyfree_evidence(**kwargs)

    assert material["packet_generation_request_status"] == ahr.P7_R54_AHR06_REQUEST_BLOCKED_STATUS_REF
    assert expected_blocker in material["execution_blocker_ids"]
    assert material["packet_generation_requested"] is False
    assert material["local_packet_generation_operation_allowed_next"] is False
    assert material["local_packet_generation_receipt_required_next"] is False
    assert material["packet_ref_ids"] == []
    assert material["next_required_step"] == ahr.P7_R54_AHR06_BLOCKED_NEXT_REQUIRED_STEP_REF
    _assert_bodyfree_no_touch(material)
    assert ahr.assert_p7_r54_ahr06_body_full_packet_generation_request_bodyfree_evidence_contract(material) is True


@pytest.mark.parametrize(
    "key,value",
    [
        ("packet_generation_request_status", "OTHER"),
        ("packet_generation_requested", False),
        ("packet_generation_requested_as_bodyfree_evidence_only", False),
        ("body_full_packet_generation_request_evidence_only", False),
        ("body_full_packet_generation_requested_here", True),
        ("body_full_generation_requested_here", True),
        ("body_full_packet_generated_here", True),
        ("body_full_packet_content_included", True),
        ("local_absolute_path_included", True),
        ("body_hash_included", True),
        ("local_packet_generation_operation_allowed_next", False),
        ("local_packet_generation_receipt_required_next", False),
        ("next_required_step", ahr.P7_R54_AHR08_STEP_REF),
        ("question_text_included", True),
        ("p8_start_allowed", True),
        ("release_allowed", True),
    ],
)
def test_r54_ahr06_rejects_request_evidence_mutations(key: str, value: object) -> None:
    mutated = deepcopy(ahr.build_p7_r54_ahr06_body_full_packet_generation_request_bodyfree_evidence())
    mutated[key] = value
    with pytest.raises(ValueError):
        ahr.assert_p7_r54_ahr06_body_full_packet_generation_request_bodyfree_evidence_contract(mutated)


def test_r54_ahr06_blocks_when_manifest_is_not_ready() -> None:
    blocked_preflight = ahr.build_p7_r54_ahr04_local_only_preflight(explicit_allow_token_ref="missing")
    blocked_manifest = ahr.build_p7_r54_ahr05_24_case_manifest_freeze(local_only_preflight=blocked_preflight)
    material = ahr.build_p7_r54_ahr06_body_full_packet_generation_request_bodyfree_evidence(
        manifest_freeze=blocked_manifest
    )

    assert material["packet_generation_request_status"] == ahr.P7_R54_AHR06_REQUEST_BLOCKED_STATUS_REF
    assert "ahr05_manifest_not_ready" in material["execution_blocker_ids"]
    assert material["packet_generation_requested"] is False
    assert material["packet_ref_ids"] == []
    assert ahr.assert_p7_r54_ahr06_body_full_packet_generation_request_bodyfree_evidence_contract(material) is True


def test_r54_ahr07_intakes_local_packet_generation_receipt_as_bodyfree_counts_only() -> None:
    request = ahr.build_p7_r54_ahr06_body_full_packet_generation_request_bodyfree_evidence()
    material = ahr.build_p7_r54_ahr07_local_packet_generation_operation_receipt_intake(
        packet_generation_request=request
    )

    assert set(material) == set(ahr.P7_R54_AHR07_LOCAL_PACKET_GENERATION_RECEIPT_REQUIRED_FIELD_REFS)
    assert material["schema_version"] == ahr.P7_R54_AHR07_LOCAL_PACKET_GENERATION_OPERATION_RECEIPT_INTAKE_SCHEMA_VERSION
    assert material["policy_section"] == ahr.P7_R54_AHR07_STEP_REF
    assert material["operation_step_ref"] == ahr.P7_R54_AHR07_STEP_REF
    assert material["ahr06_schema_version"] == ahr.P7_R54_AHR06_BODY_FULL_PACKET_GENERATION_REQUEST_BODYFREE_EVIDENCE_SCHEMA_VERSION
    assert material["ahr06_packet_generation_request_status"] == ahr.P7_R54_AHR06_REQUEST_READY_STATUS_REF
    assert material["ahr06_packet_generation_requested"] is True
    assert material["ahr06_local_packet_generation_operation_allowed_next"] is True
    assert material["ahr06_required_case_count"] == 24
    assert material["ahr06_packet_ref_id_count"] == 24
    assert len(material["ahr06_packet_ref_ids"]) == 24

    assert material["receipt_status"] == ahr.P7_R54_AHR07_RECEIPT_READY_STATUS_REF
    assert material["generation_status_ref"] == ahr.P7_R54_AHR07_RECEIPT_READY_STATUS_REF
    assert material["receipt_reason_refs"] == [ahr.P7_R54_AHR07_READY_REASON_REF]
    assert material["execution_blocker_ids"] == []
    assert material["request_ready_for_receipt_intake"] is True
    assert material["generated_case_count"] == 24
    assert material["generated_packet_count"] == 24
    assert material["generated_packet_refs_match_expected_count"] is True
    assert material["local_only"] is True
    assert material["must_not_export"] is True
    assert material["exported"] is False
    assert material["local_packet_exported"] is False
    assert material["content_included"] is False
    assert material["absolute_path_included"] is False
    assert material["hash_included"] is False
    assert material["packet_content_included"] is False
    assert material["body_full_packet_content_included"] is False
    assert material["body_full_packet_generated_here"] is False
    assert material["actual_human_review_run_here"] is False
    assert material["actual_review_execution_allowed_next"] is False
    assert material["packet_generation_operation_receipt_only"] is True
    assert material["local_packet_generation_operation_receipt_intaken"] is True
    assert material["packet_generation_receipt_intaken"] is True
    assert material["packet_completeness_export_denylist_scan_allowed_next"] is True
    assert material["actual_review_execution_blocked_until_packet_completeness_scan"] is True
    assert tuple(material["implemented_steps"]) == ahr.P7_R54_AHR07_IMPLEMENTED_STEPS
    assert tuple(material["not_yet_implemented_steps"]) == ahr.P7_R54_AHR07_NOT_YET_IMPLEMENTED_STEPS
    assert material["next_required_step"] == ahr.P7_R54_AHR08_STEP_REF
    _assert_bodyfree_no_touch(material)
    assert ahr.assert_p7_r54_ahr07_local_packet_generation_operation_receipt_intake_contract(material) is True


@pytest.mark.parametrize(
    "kwargs,expected_blocker",
    [
        ({"generated_case_count": 23}, "generated_case_count_not_24"),
        ({"generated_packet_count": 23}, "generated_packet_count_not_24"),
        ({"local_only": False}, "local_only_not_confirmed"),
        ({"must_not_export": False}, "must_not_export_not_confirmed"),
        ({"local_packet_exported": True}, "local_packet_exported"),
        ({"exported": True}, "receipt_marked_exported"),
        ({"content_included": True}, "packet_content_included"),
        ({"absolute_path_included": True}, "absolute_path_included"),
        ({"hash_included": True}, "hash_included"),
    ],
)
def test_r54_ahr07_blocks_when_receipt_is_incomplete_or_unsafe(kwargs: dict[str, object], expected_blocker: str) -> None:
    request = ahr.build_p7_r54_ahr06_body_full_packet_generation_request_bodyfree_evidence()
    material = ahr.build_p7_r54_ahr07_local_packet_generation_operation_receipt_intake(
        packet_generation_request=request,
        **kwargs,
    )

    assert material["receipt_status"] == ahr.P7_R54_AHR07_RECEIPT_BLOCKED_STATUS_REF
    assert expected_blocker in material["execution_blocker_ids"]
    assert material["local_packet_generation_operation_receipt_intaken"] is False
    assert material["packet_generation_receipt_intaken"] is False
    assert material["packet_completeness_export_denylist_scan_allowed_next"] is False
    assert material["next_required_step"] == ahr.P7_R54_AHR07_BLOCKED_NEXT_REQUIRED_STEP_REF
    assert ahr.assert_p7_r54_ahr07_local_packet_generation_operation_receipt_intake_contract(material) is True


@pytest.mark.parametrize(
    "key,value",
    [
        ("receipt_status", "OTHER"),
        ("generation_status_ref", "OTHER"),
        ("generated_case_count", 23),
        ("generated_packet_count", 23),
        ("local_packet_exported", True),
        ("content_included", True),
        ("absolute_path_included", True),
        ("hash_included", True),
        ("body_full_packet_generated_here", True),
        ("actual_human_review_run_here", True),
        ("actual_review_execution_allowed_next", True),
        ("local_packet_generation_operation_receipt_intaken", False),
        ("packet_generation_receipt_intaken", False),
        ("packet_completeness_export_denylist_scan_allowed_next", False),
        ("next_required_step", ahr.P7_R54_AHR10_STEP_REF),
        ("question_text_included", True),
        ("p8_start_allowed", True),
    ],
)
def test_r54_ahr07_rejects_receipt_mutations(key: str, value: object) -> None:
    mutated = deepcopy(ahr.build_p7_r54_ahr07_local_packet_generation_operation_receipt_intake())
    mutated[key] = value
    with pytest.raises(ValueError):
        ahr.assert_p7_r54_ahr07_local_packet_generation_operation_receipt_intake_contract(mutated)


def test_r54_ahr07_blocks_when_ahr06_request_is_blocked() -> None:
    blocked_request = ahr.build_p7_r54_ahr06_body_full_packet_generation_request_bodyfree_evidence(
        packet_generation_request_ref="missing"
    )
    material = ahr.build_p7_r54_ahr07_local_packet_generation_operation_receipt_intake(
        packet_generation_request=blocked_request
    )

    assert material["receipt_status"] == ahr.P7_R54_AHR07_RECEIPT_BLOCKED_STATUS_REF
    assert "ahr06_packet_generation_request_not_ready" in material["execution_blocker_ids"]
    assert material["local_packet_generation_operation_receipt_intaken"] is False
    assert material["next_required_step"] == ahr.P7_R54_AHR07_BLOCKED_NEXT_REQUIRED_STEP_REF
    assert ahr.assert_p7_r54_ahr07_local_packet_generation_operation_receipt_intake_contract(material) is True


def test_r54_ahr06_ahr07_design_aliases_point_to_canonical_helpers() -> None:
    request = ahr.build_p7_r54_actual_human_review_execution_bodyfree_intake_ahr06_body_full_packet_generation_request_bodyfree_evidence()
    receipt = ahr.build_p7_r54_actual_human_review_execution_bodyfree_intake_ahr07_local_packet_generation_operation_receipt_intake(
        packet_generation_request=request
    )

    assert request == ahr.build_p7_r54_actual_human_review_execution_body_full_packet_generation_request_bodyfree_evidence()
    assert ahr.assert_p7_r54_ahr06_body_full_packet_generation_request_bodyfree_contract(request) is True
    assert ahr.assert_p7_r54_actual_human_review_execution_body_full_packet_generation_request_bodyfree_evidence_contract(request) is True
    assert ahr.assert_p7_r54_ahr07_local_packet_generation_operation_receipt_intake_bodyfree_contract(receipt) is True
    assert ahr.assert_p7_r54_actual_human_review_execution_local_packet_generation_operation_receipt_intake_bodyfree_contract(receipt) is True
