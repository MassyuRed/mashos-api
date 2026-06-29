# -*- coding: utf-8 -*-
"""R54 current snapshot local review run CLR06-CLR07 contract tests."""

from __future__ import annotations

from copy import deepcopy
from typing import Any

import pytest

import emlis_ai_p7_r54_current_snapshot_local_review_run_20260627 as clr03
import emlis_ai_p7_r54_current_snapshot_local_review_run_clr04_clr05_20260627 as clr05
import emlis_ai_p7_r54_current_snapshot_local_review_run_clr06_clr07_20260627 as clr


FORBIDDEN_BODY_OR_QUESTION_KEYS = (
    "raw_input",
    "returned_emlis_body",
    "history_surface",
    "reviewer_free_text",
    "reviewer_note",
    "reviewer_notes",
    "question_text",
    "draft_question_text",
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


def _ready_request() -> dict[str, Any]:
    material = clr.build_p7_r54_clr06_body_full_packet_generation_request_bodyfree_evidence()
    assert clr.assert_p7_r54_clr06_body_full_packet_generation_request_bodyfree_evidence_contract(material) is True
    return material


def _ready_receipt(request: dict[str, Any]) -> dict[str, Any]:
    return clr.build_p7_r54_clr07_bodyfree_generated_receipt_from_request(request)


def test_r54_clr00_to_clr05_are_present_before_clr06_clr07() -> None:
    preflight = clr05.build_p7_r54_clr04_local_only_preflight()
    manifest = clr05.build_p7_r54_clr05_24_case_manifest_freeze(local_only_preflight=preflight)

    assert clr05.assert_p7_r54_clr04_local_only_preflight_contract(preflight) is True
    assert clr05.assert_p7_r54_clr05_24_case_manifest_freeze_contract(manifest) is True
    assert manifest["manifest_status"] == clr05.P7_R54_CLR05_MANIFEST_READY_STATUS_REF
    assert manifest["manifest_row_count"] == 24
    assert manifest["body_full_packet_generation_request_allowed_next"] is True
    assert manifest["next_required_step"] == clr.P7_R54_CLR06_STEP_REF


def test_r54_clr06_records_packet_generation_request_evidence_without_generating_packet_material() -> None:
    manifest = clr05.build_p7_r54_clr05_24_case_manifest_freeze()
    material = clr.build_p7_r54_clr06_body_full_packet_generation_request_bodyfree_evidence(
        case_manifest_freeze=manifest
    )

    assert set(material) == set(clr.P7_R54_CLR06_BODY_FULL_PACKET_GENERATION_REQUEST_BODYFREE_EVIDENCE_REQUIRED_FIELD_REFS)
    assert material["schema_version"] == clr.P7_R54_CLR06_BODY_FULL_PACKET_GENERATION_REQUEST_BODYFREE_EVIDENCE_SCHEMA_VERSION
    assert material["policy_section"] == clr.P7_R54_CLR06_STEP_REF
    assert material["operation_step_ref"] == clr.P7_R54_CLR06_STEP_REF
    assert material["clr05_next_required_step"] == clr.P7_R54_CLR06_STEP_REF
    assert material["clr05_manifest_status"] == clr05.P7_R54_CLR05_MANIFEST_READY_STATUS_REF
    assert material["clr05_manifest_ready"] is True
    assert material["clr05_manifest_row_count"] == 24
    assert material["clr05_manifest_rows_bodyfree_only"] is True

    assert material["existing_op06_current_refs_are_historical_here"] is True
    assert material["existing_op06_reused_as_actual_request_basis"] is False
    assert material["existing_op06_structural_contract_reused"] is True
    assert material["packet_generation_request_status"] == clr.P7_R54_CLR06_REQUEST_READY_STATUS_REF
    assert material["packet_generation_request_status_ref"] == clr.P7_R54_CLR06_PACKET_GENERATION_REQUEST_STATUS_REF
    assert material["packet_generation_request_ref"] == clr.P7_R54_CLR06_PACKET_GENERATION_REQUEST_REF
    assert material["packet_generation_request_policy_ref"] == clr.P7_R54_CLR06_PACKET_GENERATION_REQUEST_POLICY_REF
    assert material["packet_generation_request_reason_refs"] == [clr.P7_R54_CLR06_READY_REASON_REF]
    assert material["execution_blocker_ids"] == []
    assert material["open_execution_blocker_ids"] == []
    assert material["packet_request_count"] == 24
    assert material["packet_ref_count"] == 24
    assert material["expected_packet_ref_count"] == 24
    assert material["packet_ref_ids"] == manifest["packet_ref_ids"]
    assert material["packet_ref_ids_unique"] is True
    assert material["packet_generation_request_row_count"] == 24
    assert material["request_is_bodyfree_only"] is True
    assert material["allowed_output_ref"] == clr.P7_R54_CLR06_ALLOWED_OUTPUT_REF
    assert tuple(material["forbidden_output_refs"]) == clr.P7_R54_CLR06_FORBIDDEN_OUTPUT_REFS
    assert tuple(material["export_denylist_refs"]) == clr05.P7_R54_CLR04_EXPORT_DENYLIST_REFS

    assert len(material["packet_generation_request_rows"]) == 24
    for index, row in enumerate(material["packet_generation_request_rows"], start=1):
        assert set(row) == set(clr.P7_R54_CLR06_PACKET_REQUEST_ROW_REQUIRED_FIELD_REFS)
        assert row["case_index"] == index
        assert row["packet_generation_requested"] is True
        assert row["request_is_bodyfree_only"] is True
        assert row["allowed_output_ref"] == clr.P7_R54_CLR06_ALLOWED_OUTPUT_REF
        assert tuple(row["forbidden_output_refs"]) == clr.P7_R54_CLR06_FORBIDDEN_OUTPUT_REFS
        for false_key in (
            "packet_content_included",
            "raw_body_included",
            "returned_emlis_body_included",
            "history_surface_included",
            "reviewer_free_text_included",
            "local_path_included",
            "local_absolute_path_included",
            "body_hash_included",
            "question_text_included",
            "draft_question_text_included",
            "terminal_output_body_included",
        ):
            assert row[false_key] is False
        assert row["body_free"] is True
        for forbidden_key in FORBIDDEN_BODY_OR_QUESTION_KEYS:
            assert forbidden_key not in row

    for false_key in (
        "request_contains_packet_content",
        "request_contains_local_path",
        "request_contains_local_absolute_path",
        "request_contains_body_hash",
        "request_contains_raw_body",
        "request_contains_returned_body",
        "request_contains_history_surface",
        "request_contains_reviewer_free_text",
        "request_contains_question_text",
        "request_contains_draft_question_text",
        "request_contains_terminal_output_body",
        "body_full_packet_generation_local_operation_started_here",
        "body_full_packet_generated_here",
        "body_full_packet_export_allowed",
        "body_full_packet_zip_inclusion_allowed",
        "local_review_root_path_included",
        "local_packet_directory_path_included",
        "body_full_packet_content_included",
        "actual_review_evidence_complete",
        "actual_human_review_run_here",
        "disposal_verified_before_receipt",
    ):
        assert material[false_key] is False
    assert material["body_full_packet_generation_request_evidence_materialized_here"] is True
    assert material["local_packet_generation_operation_receipt_intake_allowed_next"] is True
    assert material["p5_actual_review_still_not_run"] is True
    assert material["rating_row_count"] == 0
    assert material["question_observation_row_count"] == 0
    assert tuple(material["implemented_steps"]) == clr.P7_R54_CLR06_IMPLEMENTED_STEPS
    assert tuple(material["not_yet_implemented_steps"]) == clr.P7_R54_CLR06_NOT_YET_IMPLEMENTED_STEPS
    assert material["next_required_step"] == clr.P7_R54_CLR07_STEP_REF
    _assert_bodyfree_no_touch(material)
    assert clr.assert_p7_r54_clr06_body_full_packet_generation_request_bodyfree_evidence_contract(material) is True


def test_r54_clr06_blocks_request_when_manifest_is_not_ready() -> None:
    preflight = clr05.build_p7_r54_clr04_local_only_preflight(explicit_local_only_allow_ref="missing")
    manifest = clr05.build_p7_r54_clr05_24_case_manifest_freeze(local_only_preflight=preflight)
    material = clr.build_p7_r54_clr06_body_full_packet_generation_request_bodyfree_evidence(
        case_manifest_freeze=manifest
    )

    assert material["packet_generation_request_status"] == clr.P7_R54_CLR06_REQUEST_BLOCKED_STATUS_REF
    assert material["packet_generation_request_ref"] == "not_requested_until_clr05_manifest_ready"
    assert material["clr05_manifest_ready"] is False
    assert material["packet_request_count"] == 0
    assert material["packet_ref_ids"] == []
    assert material["packet_ref_count"] == 0
    assert material["packet_generation_request_rows"] == []
    assert material["packet_generation_request_row_count"] == 0
    assert material["body_full_packet_generation_request_evidence_materialized_here"] is False
    assert material["local_packet_generation_operation_receipt_intake_allowed_next"] is False
    assert "r54_clr06_blocked_until_24_case_manifest_ready" in material["execution_blocker_ids"]
    assert material["body_full_packet_generated_here"] is False
    assert material["actual_human_review_run_here"] is False
    assert tuple(material["implemented_steps"]) == clr05.P7_R54_CLR04_IMPLEMENTED_STEPS
    assert tuple(material["not_yet_implemented_steps"]) == clr05.P7_R54_CLR04_NOT_YET_IMPLEMENTED_STEPS
    assert material["next_required_step"] == clr.P7_R54_CLR06_BLOCKED_NEXT_REQUIRED_STEP_REF
    _assert_bodyfree_no_touch(material)
    assert clr.assert_p7_r54_clr06_body_full_packet_generation_request_bodyfree_evidence_contract(material) is True


def test_r54_clr07_intakes_local_packet_generation_receipt_bodyfree_without_exposing_packet() -> None:
    request = _ready_request()
    receipt = _ready_receipt(request)
    material = clr.build_p7_r54_clr07_local_packet_generation_operation_receipt_intake(
        body_full_packet_generation_request_bodyfree_evidence=request,
        packet_generation_operation_receipt=receipt,
    )

    assert set(material) == set(clr.P7_R54_CLR07_LOCAL_PACKET_GENERATION_OPERATION_RECEIPT_INTAKE_REQUIRED_FIELD_REFS)
    assert material["schema_version"] == clr.P7_R54_CLR07_LOCAL_PACKET_GENERATION_OPERATION_RECEIPT_INTAKE_SCHEMA_VERSION
    assert material["policy_section"] == clr.P7_R54_CLR07_STEP_REF
    assert material["operation_step_ref"] == clr.P7_R54_CLR07_STEP_REF
    assert material["clr06_next_required_step"] == clr.P7_R54_CLR07_STEP_REF
    assert material["clr06_packet_generation_request_status"] == clr.P7_R54_CLR06_REQUEST_READY_STATUS_REF
    assert material["clr06_request_ready"] is True

    assert material["existing_op07_current_refs_are_historical_here"] is True
    assert material["existing_op07_reused_as_actual_local_operation_basis"] is False
    assert material["existing_op07_structural_contract_reused"] is True
    assert material["packet_generation_operation_ref"] == clr.P7_R54_CLR07_PACKET_GENERATION_OPERATION_REF
    assert material["packet_generation_status"] == clr.P7_R54_CLR07_LOCAL_ONLY_PACKET_GENERATED_STATUS_REF
    assert material["packet_generation_receipt_status_ref"] == clr.P7_R54_CLR07_RECEIPT_READY_STATUS_REF
    assert material["packet_generation_receipt_policy_ref"] == clr.P7_R54_CLR07_PACKET_GENERATION_RECEIPT_POLICY_REF
    assert material["packet_generation_receipt_reason_refs"] == [clr.P7_R54_CLR07_READY_REASON_REF]
    assert tuple(material["receipt_allowed_field_refs"]) == clr.P7_R54_CLR07_RECEIPT_ALLOWED_FIELD_REFS
    assert material["receipt_allowed_field_ref_count"] == len(clr.P7_R54_CLR07_RECEIPT_ALLOWED_FIELD_REFS)
    assert material["expected_packet_count"] == 24
    assert material["expected_packet_ref_ids"] == request["packet_ref_ids"]
    assert material["expected_packet_ref_count"] == 24
    assert material["actual_packet_count"] == 24
    assert material["packet_ref_ids"] == request["packet_ref_ids"]
    assert material["packet_ref_count"] == 24
    assert material["packet_ref_ids_unique"] is True
    assert material["packet_ref_ids_match_request"] is True
    assert material["export_candidate_count"] == 0
    assert material["local_packet_export_candidate_count"] == 0
    assert material["execution_blocker_ids"] == []

    for false_key in (
        "receipt_contains_packet_content",
        "receipt_contains_local_path",
        "receipt_contains_local_absolute_path",
        "receipt_contains_body_hash",
        "receipt_contains_raw_body",
        "receipt_contains_returned_body",
        "receipt_contains_history_surface",
        "receipt_contains_reviewer_free_text",
        "receipt_contains_question_text",
        "receipt_contains_draft_question_text",
        "receipt_contains_terminal_output_body",
        "local_operation_receipt_body_stored_here",
        "body_full_packet_content_included",
        "body_full_packet_generated_here",
        "actual_body_full_packet_generated_here",
        "local_reviewer_payload_materialized_here",
        "local_review_root_path_included",
        "local_packet_directory_path_included",
        "local_packet_exported",
        "body_full_packet_export_allowed",
        "body_full_packet_zip_inclusion_allowed",
        "reviewer_notes_export_allowed",
        "actual_review_evidence_complete",
        "actual_human_review_run_here",
        "disposal_verified_before_receipt",
    ):
        assert material[false_key] is False
    assert material["receipt_is_bodyfree_only"] is True
    assert material["packet_generation_local_operation_declared_complete"] is True
    assert material["packet_generation_local_operation_unverified_by_artifact"] is True
    assert material["local_operation_executed_outside_artifact_boundary"] is True
    assert material["local_operation_receipt_materialized_here"] is True
    assert material["packet_completeness_export_denylist_scan_allowed_next"] is True
    assert material["actual_review_execution_blocked_until_packet_scan"] is True
    assert material["p5_actual_review_still_not_run"] is True
    assert material["rating_row_count"] == 0
    assert material["question_observation_row_count"] == 0
    assert tuple(material["implemented_steps"]) == clr.P7_R54_CLR07_IMPLEMENTED_STEPS
    assert tuple(material["not_yet_implemented_steps"]) == clr.P7_R54_CLR07_NOT_YET_IMPLEMENTED_STEPS
    assert material["next_required_step"] == clr.P7_R54_CLR08_STEP_REF
    _assert_bodyfree_no_touch(material)
    assert clr.assert_p7_r54_clr07_local_packet_generation_operation_receipt_intake_contract(material) is True


def test_r54_clr07_blocks_when_receipt_is_missing() -> None:
    request = _ready_request()
    material = clr.build_p7_r54_clr07_local_packet_generation_operation_receipt_intake(
        body_full_packet_generation_request_bodyfree_evidence=request
    )

    assert material["packet_generation_status"] == clr.P7_R54_CLR07_PACKET_GENERATION_BLOCKED_STATUS_REF
    assert material["packet_generation_receipt_status_ref"] == clr.P7_R54_CLR07_RECEIPT_BLOCKED_STATUS_REF
    assert "local_packet_generation_operation_receipt_missing" in material["execution_blocker_ids"]
    assert material["packet_completeness_export_denylist_scan_allowed_next"] is False
    assert material["local_operation_receipt_materialized_here"] is False
    assert material["body_full_packet_generated_here"] is False
    assert material["actual_human_review_run_here"] is False
    assert tuple(material["implemented_steps"]) == clr.P7_R54_CLR06_IMPLEMENTED_STEPS
    assert tuple(material["not_yet_implemented_steps"]) == clr.P7_R54_CLR06_NOT_YET_IMPLEMENTED_STEPS
    assert material["next_required_step"] == clr.P7_R54_CLR07_BLOCKED_NEXT_REQUIRED_STEP_REF
    _assert_bodyfree_no_touch(material)
    assert clr.assert_p7_r54_clr07_local_packet_generation_operation_receipt_intake_contract(material) is True


@pytest.mark.parametrize(
    "receipt_mutation,expected_status,expected_blocker",
    [
        (
            {"packet_generation_status": clr.P7_R54_CLR07_PACKET_GENERATION_PARTIAL_STATUS_REF},
            clr.P7_R54_CLR07_PACKET_GENERATION_PARTIAL_STATUS_REF,
            "local_packet_generation_operation_receipt_partial",
        ),
        (
            {"packet_generation_status": clr.P7_R54_CLR07_PACKET_GENERATION_BLOCKED_STATUS_REF},
            clr.P7_R54_CLR07_PACKET_GENERATION_BLOCKED_STATUS_REF,
            "local_packet_generation_operation_receipt_blocked",
        ),
        (
            {"packet_ref_ids": [f"p7r48-p5-packet-r54clr-{index:03d}" for index in range(1, 24)]},
            clr.P7_R54_CLR07_PACKET_GENERATION_BLOCKED_STATUS_REF,
            "local_packet_generation_packet_refs_missing_or_mismatched",
        ),
        (
            {"actual_packet_count": 23},
            clr.P7_R54_CLR07_PACKET_GENERATION_BLOCKED_STATUS_REF,
            "local_packet_generation_actual_packet_count_mismatched",
        ),
        (
            {"export_candidate_count": 1},
            clr.P7_R54_CLR07_PACKET_GENERATION_BLOCKED_STATUS_REF,
            "body_payload_leak_detected",
        ),
    ],
)
def test_r54_clr07_blocks_or_partials_receipt_when_receipt_is_not_clean(
    receipt_mutation: dict[str, object], expected_status: str, expected_blocker: str
) -> None:
    request = _ready_request()
    receipt = _ready_receipt(request)
    receipt.update(receipt_mutation)
    material = clr.build_p7_r54_clr07_local_packet_generation_operation_receipt_intake(
        body_full_packet_generation_request_bodyfree_evidence=request,
        packet_generation_operation_receipt=receipt,
    )

    assert material["packet_generation_status"] == expected_status
    assert expected_blocker in material["execution_blocker_ids"]
    assert material["packet_completeness_export_denylist_scan_allowed_next"] is False
    assert material["packet_generation_local_operation_declared_complete"] is False
    assert material["body_full_packet_generated_here"] is False
    assert material["actual_human_review_run_here"] is False
    assert tuple(material["implemented_steps"]) == clr.P7_R54_CLR06_IMPLEMENTED_STEPS
    assert tuple(material["not_yet_implemented_steps"]) == clr.P7_R54_CLR06_NOT_YET_IMPLEMENTED_STEPS
    assert material["next_required_step"] == clr.P7_R54_CLR07_BLOCKED_NEXT_REQUIRED_STEP_REF
    _assert_bodyfree_no_touch(material)
    assert clr.assert_p7_r54_clr07_local_packet_generation_operation_receipt_intake_contract(material) is True


@pytest.mark.parametrize(
    "builder,asserter,key,value",
    [
        (
            clr.build_p7_r54_clr06_body_full_packet_generation_request_bodyfree_evidence,
            clr.assert_p7_r54_clr06_body_full_packet_generation_request_bodyfree_evidence_contract,
            "request_contains_packet_content",
            True,
        ),
        (
            clr.build_p7_r54_clr06_body_full_packet_generation_request_bodyfree_evidence,
            clr.assert_p7_r54_clr06_body_full_packet_generation_request_bodyfree_evidence_contract,
            "body_full_packet_generated_here",
            True,
        ),
        (
            clr.build_p7_r54_clr06_body_full_packet_generation_request_bodyfree_evidence,
            clr.assert_p7_r54_clr06_body_full_packet_generation_request_bodyfree_evidence_contract,
            "p8_start_allowed",
            True,
        ),
        (
            lambda: clr.build_p7_r54_clr07_local_packet_generation_operation_receipt_intake(
                body_full_packet_generation_request_bodyfree_evidence=_ready_request(),
                packet_generation_operation_receipt=_ready_receipt(_ready_request()),
            ),
            clr.assert_p7_r54_clr07_local_packet_generation_operation_receipt_intake_contract,
            "receipt_contains_packet_content",
            True,
        ),
        (
            lambda: clr.build_p7_r54_clr07_local_packet_generation_operation_receipt_intake(
                body_full_packet_generation_request_bodyfree_evidence=_ready_request(),
                packet_generation_operation_receipt=_ready_receipt(_ready_request()),
            ),
            clr.assert_p7_r54_clr07_local_packet_generation_operation_receipt_intake_contract,
            "actual_body_full_packet_generated_here",
            True,
        ),
        (
            lambda: clr.build_p7_r54_clr07_local_packet_generation_operation_receipt_intake(
                body_full_packet_generation_request_bodyfree_evidence=_ready_request(),
                packet_generation_operation_receipt=_ready_receipt(_ready_request()),
            ),
            clr.assert_p7_r54_clr07_local_packet_generation_operation_receipt_intake_contract,
            "release_allowed",
            True,
        ),
    ],
)
def test_r54_clr06_clr07_reject_bodyfull_review_or_promotion_mutations(
    builder: Any, asserter: Any, key: str, value: object
) -> None:
    material = builder()
    mutated = deepcopy(material)
    mutated[key] = value
    with pytest.raises(ValueError):
        asserter(mutated)


def test_r54_clr06_clr07_reject_forbidden_payload_or_question_keys() -> None:
    request = _ready_request()
    mutated_request = deepcopy(request)
    mutated_request["packet_content"] = "forbidden"
    with pytest.raises(ValueError):
        clr.assert_p7_r54_clr06_body_full_packet_generation_request_bodyfree_evidence_contract(mutated_request)

    forbidden_receipt = _ready_receipt(request)
    forbidden_receipt["local_absolute_path"] = "forbidden"
    with pytest.raises(ValueError):
        clr.build_p7_r54_clr07_local_packet_generation_operation_receipt_intake(
            body_full_packet_generation_request_bodyfree_evidence=request,
            packet_generation_operation_receipt=forbidden_receipt,
        )

    ready_receipt = _ready_receipt(request)
    material = clr.build_p7_r54_clr07_local_packet_generation_operation_receipt_intake(
        body_full_packet_generation_request_bodyfree_evidence=request,
        packet_generation_operation_receipt=ready_receipt,
    )
    mutated_material = deepcopy(material)
    mutated_material["question_text"] = "forbidden"
    with pytest.raises(ValueError):
        clr.assert_p7_r54_clr07_local_packet_generation_operation_receipt_intake_contract(mutated_material)


def test_r54_clr07_rejects_receipt_with_unsupported_safe_but_unlisted_field() -> None:
    request = _ready_request()
    receipt = _ready_receipt(request)
    receipt["unlisted_safe_ref"] = "not_allowed"
    with pytest.raises(ValueError):
        clr.build_p7_r54_clr07_local_packet_generation_operation_receipt_intake(
            body_full_packet_generation_request_bodyfree_evidence=request,
            packet_generation_operation_receipt=receipt,
        )


def test_r54_clr06_clr07_aliases_remain_available() -> None:
    request = clr.build_p7_r54_current_snapshot_local_run_clr06_body_full_packet_generation_request_bodyfree_evidence()
    assert (
        clr.assert_p7_r54_current_snapshot_local_run_clr06_body_full_packet_generation_request_bodyfree_evidence_contract(
            request
        )
        is True
    )
    assert clr.assert_p7_r54_current_snapshot_body_full_packet_generation_request_bodyfree_evidence_contract(request) is True

    receipt = clr.build_p7_r54_clr07_bodyfree_generated_receipt_from_request(request)
    material = clr.build_p7_r54_current_snapshot_local_run_clr07_local_packet_generation_operation_receipt_intake(
        body_full_packet_generation_request_bodyfree_evidence=request,
        packet_generation_operation_receipt=receipt,
    )
    assert clr.assert_p7_r54_current_snapshot_local_run_clr07_local_packet_generation_operation_receipt_intake_contract(material) is True
    assert clr.assert_p7_r54_current_snapshot_local_packet_generation_operation_receipt_intake_bodyfree_contract(material) is True
