# -*- coding: utf-8 -*-
"""R54-AHR-CR06/CR07 current received actual local review operation tests."""

from __future__ import annotations

from copy import deepcopy

import pytest

import emlis_ai_p7_r54_ahr_current_received_snapshot_actual_local_review_operation_20260628 as cr


def _assert_bodyfree_no_touch(material: dict[str, object]) -> None:
    assert material["body_free"] is True
    for key in cr.P7_R54_AHR_CR_FALSE_FLAG_REFS:
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


def test_cr06_blocks_by_default_when_cr05_preflight_lacks_explicit_allow() -> None:
    material = cr.build_p7_r54_ahr_cr06_packet_generation_request_bridge()

    assert set(material) == set(cr.P7_R54_AHR_CR06_PACKET_GENERATION_REQUEST_BRIDGE_REQUIRED_FIELD_REFS)
    assert material["schema_version"] == cr.P7_R54_AHR_CR_PACKET_GENERATION_REQUEST_BRIDGE_SCHEMA_VERSION
    assert material["policy_section"] == cr.P7_R54_AHR_CR06_STEP_REF
    assert material["operation_step_ref"] == cr.P7_R54_AHR_CR06_STEP_REF
    assert material["cr05_schema_version"] == cr.P7_R54_AHR_CR_LOCAL_ONLY_PREFLIGHT_SCHEMA_VERSION
    assert material["cr05_next_required_step"] == cr.P7_R54_AHR_CR05_DEFAULT_BLOCKED_NEXT_REQUIRED_STEP_REF
    assert material["cr05_preflight_ready"] is False
    assert material["cr05_body_full_packet_generation_allowed_by_preflight"] is False
    assert material["cr05_actual_review_operation_allowed_by_preflight"] is False
    assert material["cr05_explicit_allow_ref_present"] is False

    assert material["packet_generation_request_bridge_status_ref"] == cr.P7_R54_AHR_CR06_PACKET_REQUEST_BLOCKED_STATUS_REF
    assert tuple(material["packet_generation_request_bridge_allowed_status_refs"]) == cr.P7_R54_AHR_CR06_ALLOWED_PACKET_REQUEST_STATUS_REFS
    assert material["packet_generation_request_bridge_ready"] is False
    assert material["packet_generation_request_bridge_reason_refs"] == []
    assert material["packet_generation_request_bridge_blocker_refs"] == [
        cr.P7_R54_AHR_CR06_PREFLIGHT_NOT_READY_BLOCKER_REF,
        cr.P7_R54_AHR_CR06_PACKET_NOT_ALLOWED_BY_PREFLIGHT_BLOCKER_REF,
        cr.P7_R54_AHR_CR06_ACTUAL_OPERATION_NOT_ALLOWED_BY_PREFLIGHT_BLOCKER_REF,
        cr.P7_R54_AHR_CR06_EXPLICIT_ALLOW_MISSING_BLOCKER_REF,
    ]
    assert material["packet_generation_request_bridge_blocker_ref_count"] == 4
    assert material["packet_generation_request_ref"] == ""
    assert material["packet_generation_request_ref_present"] is False
    assert material["packet_generation_allowed_by_preflight"] is False
    assert material["next_required_step"] == cr.P7_R54_AHR_CR06_DEFAULT_BLOCKED_NEXT_REQUIRED_STEP_REF
    _assert_bodyfree_no_touch(material)
    assert cr.assert_p7_r54_ahr_cr06_packet_generation_request_bridge_contract(material) is True


def test_cr06_ready_preflight_creates_only_bodyfree_request_ref_not_packet_body() -> None:
    material = _cr06_ready()

    assert set(material) == set(cr.P7_R54_AHR_CR06_PACKET_GENERATION_REQUEST_BRIDGE_REQUIRED_FIELD_REFS)
    assert material["cr05_next_required_step"] == cr.P7_R54_AHR_CR06_STEP_REF
    assert material["cr05_preflight_ready"] is True
    assert material["cr05_body_full_packet_generation_allowed_by_preflight"] is True
    assert material["cr05_actual_review_operation_allowed_by_preflight"] is True
    assert material["cr05_local_only"] is True
    assert material["cr05_must_not_export"] is True
    assert material["cr05_explicit_allow_ref_present"] is True
    assert material["cr05_body_full_packet_export_allowed"] is False
    assert material["cr05_body_full_packet_content_included"] is False
    assert material["cr05_body_full_packet_generated_here"] is False
    assert material["cr05_actual_human_review_run_here"] is False

    assert material["actual_review_basis_ref"] == "current_received_snapshot_264_85_258_171"
    assert material["historical_ahr_basis_ref"] == "current_received_snapshot_260_83_256_169"
    assert material["historical_cs_basis_ref"] == "current_received_snapshot_262_84_257_170"
    assert material["packet_generation_request_bridge_status_ref"] == cr.P7_R54_AHR_CR06_PACKET_REQUEST_READY_STATUS_REF
    assert material["packet_generation_request_bridge_ready"] is True
    assert material["packet_generation_request_bridge_reason_refs"] == [cr.P7_R54_AHR_CR06_READY_REASON_REF]
    assert material["packet_generation_request_bridge_blocker_refs"] == []
    assert material["packet_generation_request_ref"] == cr.P7_R54_AHR_CR06_DEFAULT_PACKET_GENERATION_REQUEST_REF
    assert material["packet_generation_request_ref_present"] is True
    assert material["packet_generation_allowed_by_preflight"] is True
    assert material["packet_generation_started_here"] is False
    assert material["body_full_packet_generation_started_here"] is False
    assert material["body_full_packet_generated_here"] is False
    assert material["body_full_packet_content_included"] is False
    assert material["local_absolute_path_included"] is False
    assert material["body_hash_included"] is False
    assert material["terminal_output_body_included"] is False
    assert material["request_bridge_requires_cr05_ready_preflight"] is True
    assert material["request_bridge_does_not_generate_packet_body"] is True
    assert material["request_bridge_does_not_materialize_local_packet"] is True
    assert material["request_bridge_does_not_execute_actual_human_review"] is True
    assert material["request_bridge_does_not_create_review_rows"] is True
    assert material["request_bridge_does_not_create_disposal_receipt"] is True
    assert material["request_bridge_keeps_request_receipt_refs_bodyfree"] is True
    assert tuple(material["implemented_steps"]) == cr.P7_R54_AHR_CR06_IMPLEMENTED_STEPS
    assert tuple(material["not_yet_implemented_steps"]) == cr.P7_R54_AHR_CR06_NOT_YET_IMPLEMENTED_STEPS
    assert material["next_required_step"] == cr.P7_R54_AHR_CR07_STEP_REF
    _assert_bodyfree_no_touch(material)
    assert cr.assert_p7_r54_ahr_cr06_packet_generation_request_bridge_contract(material) is True


@pytest.mark.parametrize(
    "kwargs,expected_blocker",
    [
        ({"local_only": False}, cr.P7_R54_AHR_CR06_PREFLIGHT_NOT_READY_BLOCKER_REF),
        ({"must_not_export": False}, cr.P7_R54_AHR_CR06_PREFLIGHT_NOT_READY_BLOCKER_REF),
        ({"local_review_root_ref": ""}, cr.P7_R54_AHR_CR06_PREFLIGHT_NOT_READY_BLOCKER_REF),
        ({"explicit_allow_ref": ""}, cr.P7_R54_AHR_CR06_EXPLICIT_ALLOW_MISSING_BLOCKER_REF),
        ({"retention_policy_ref": ""}, cr.P7_R54_AHR_CR06_PREFLIGHT_NOT_READY_BLOCKER_REF),
        ({"disposal_policy_ref": ""}, cr.P7_R54_AHR_CR06_PREFLIGHT_NOT_READY_BLOCKER_REF),
        ({"export_denylist_policy_ref": ""}, cr.P7_R54_AHR_CR06_PREFLIGHT_NOT_READY_BLOCKER_REF),
        ({"body_full_packet_export_allowed": True}, cr.P7_R54_AHR_CR06_BODYFULL_EXPORT_ALLOWED_BLOCKER_REF),
    ],
)
def test_cr06_blocks_when_cr05_ready_conditions_are_not_met(
    kwargs: dict[str, object], expected_blocker: str
) -> None:
    params: dict[str, object] = {"explicit_allow_ref": cr.P7_R54_AHR_CR05_DEFAULT_EXPLICIT_ALLOW_REF}
    params.update(kwargs)
    cr05 = cr.build_p7_r54_ahr_cr05_local_only_preflight(**params)
    material = cr.build_p7_r54_ahr_cr06_packet_generation_request_bridge(local_only_preflight=cr05)

    assert material["packet_generation_request_bridge_ready"] is False
    assert expected_blocker in material["packet_generation_request_bridge_blocker_refs"]
    assert material["packet_generation_request_ref_present"] is False
    assert material["packet_generation_allowed_by_preflight"] is False
    assert material["packet_generation_started_here"] is False
    assert material["body_full_packet_generated_here"] is False
    assert material["actual_human_review_run_here"] is False
    assert material["next_required_step"] == cr.P7_R54_AHR_CR06_DEFAULT_BLOCKED_NEXT_REQUIRED_STEP_REF
    assert cr.assert_p7_r54_ahr_cr06_packet_generation_request_bridge_contract(material) is True


@pytest.mark.parametrize(
    "key,value",
    [
        ("cr05_schema_version", "changed"),
        ("cr05_next_required_step", "not_cr06"),
        ("cr05_preflight_ready", False),
        ("cr05_body_full_packet_generation_allowed_by_preflight", False),
        ("cr05_actual_review_operation_allowed_by_preflight", False),
        ("cr05_explicit_allow_ref_present", False),
        ("cr05_body_full_packet_export_allowed", True),
        ("cr05_body_full_packet_content_included", True),
        ("cr05_body_full_packet_generated_here", True),
        ("cr05_actual_human_review_run_here", True),
        ("packet_generation_request_bridge_allowed_status_refs", ["changed"]),
        ("packet_generation_request_bridge_status_ref", cr.P7_R54_AHR_CR06_PACKET_REQUEST_BLOCKED_STATUS_REF),
        ("packet_generation_request_bridge_ready", False),
        ("packet_generation_request_bridge_reason_refs", []),
        ("packet_generation_request_bridge_blocker_refs", ["blocked"]),
        ("packet_generation_request_bridge_blocker_ref_count", 99),
        ("packet_generation_request_ref", ""),
        ("packet_generation_request_ref_present", False),
        ("packet_generation_allowed_by_preflight", False),
        ("packet_generation_started_here", True),
        ("body_full_packet_generation_started_here", True),
        ("body_full_packet_generated_here", True),
        ("body_full_packet_content_included", True),
        ("local_absolute_path_included", True),
        ("body_hash_included", True),
        ("terminal_output_body_included", True),
        ("request_bridge_requires_cr05_ready_preflight", False),
        ("request_bridge_does_not_generate_packet_body", False),
        ("request_bridge_does_not_materialize_local_packet", False),
        ("request_bridge_does_not_execute_actual_human_review", False),
        ("request_bridge_does_not_create_review_rows", False),
        ("request_bridge_does_not_create_disposal_receipt", False),
        ("request_bridge_keeps_request_receipt_refs_bodyfree", False),
        ("actual_human_review_run_here", True),
        ("actual_human_review_complete", True),
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
        ("next_required_step", "not_cr07"),
    ],
)
def test_cr06_rejects_request_bridge_mutations_or_execution_promotion(key: str, value: object) -> None:
    mutated = deepcopy(_cr06_ready())
    mutated[key] = value
    with pytest.raises(ValueError):
        cr.assert_p7_r54_ahr_cr06_packet_generation_request_bridge_contract(mutated)


def test_cr06_rejects_forbidden_body_or_question_key_in_material() -> None:
    mutated = deepcopy(_cr06_ready())
    mutated["packet_content"] = "must not be exported"
    with pytest.raises(ValueError):
        cr.assert_p7_r54_ahr_cr06_packet_generation_request_bridge_contract(mutated)


def test_cr07_blocks_without_receipt_input_even_when_cr06_is_ready() -> None:
    material = cr.build_p7_r54_ahr_cr07_packet_generation_receipt_and_scan(packet_generation_request_bridge=_cr06_ready())

    assert set(material) == set(cr.P7_R54_AHR_CR07_PACKET_GENERATION_RECEIPT_SCAN_REQUIRED_FIELD_REFS)
    assert material["schema_version"] == cr.P7_R54_AHR_CR_PACKET_GENERATION_RECEIPT_SCAN_SCHEMA_VERSION
    assert material["policy_section"] == cr.P7_R54_AHR_CR07_STEP_REF
    assert material["operation_step_ref"] == cr.P7_R54_AHR_CR07_STEP_REF
    assert material["cr06_schema_version"] == cr.P7_R54_AHR_CR_PACKET_GENERATION_REQUEST_BRIDGE_SCHEMA_VERSION
    assert material["cr06_next_required_step"] == cr.P7_R54_AHR_CR07_STEP_REF
    assert material["cr06_packet_generation_request_bridge_ready"] is True
    assert material["cr06_packet_generation_request_ref_present"] is True

    assert material["packet_generation_receipt_status_ref"] == cr.P7_R54_AHR_CR07_PACKET_RECEIPT_BLOCKED_STATUS_REF
    assert tuple(material["packet_generation_receipt_allowed_status_refs"]) == cr.P7_R54_AHR_CR07_ALLOWED_PACKET_RECEIPT_STATUS_REFS
    assert material["packet_generation_receipt_ready"] is False
    assert material["packet_generation_receipt_reason_refs"] == []
    assert material["packet_generation_receipt_blocker_refs"] == [cr.P7_R54_AHR_CR07_RECEIPT_INPUT_MISSING_BLOCKER_REF]
    assert material["packet_generation_receipt_blocker_ref_count"] == 1
    assert material["packet_generation_receipt_input_provided"] is False
    assert material["receipt_input_forbidden_key_detected"] is False
    assert material["packet_generation_receipt_ref"] == ""
    assert material["packet_generation_receipt_ref_present"] is False
    assert material["packet_case_count"] == 0
    assert material["packet_case_count_matches_manifest"] is False
    assert material["packet_completeness_scan_ref"] == ""
    assert material["packet_completeness_scan_ref_present"] is False
    assert material["packet_completeness_passed"] is False
    assert material["export_denylist_scan_ref"] == ""
    assert material["export_denylist_scan_ref_present"] is False
    assert material["export_denylist_scan_passed"] is False
    assert material["next_required_step"] == cr.P7_R54_AHR_CR07_DEFAULT_BLOCKED_NEXT_REQUIRED_STEP_REF
    _assert_bodyfree_no_touch(material)
    assert cr.assert_p7_r54_ahr_cr07_packet_generation_receipt_and_scan_contract(material) is True


def test_cr07_accepts_bodyfree_receipt_counts_and_scan_refs_without_packet_body() -> None:
    material = _cr07_ready()

    assert set(material) == set(cr.P7_R54_AHR_CR07_PACKET_GENERATION_RECEIPT_SCAN_REQUIRED_FIELD_REFS)
    assert material["cr06_packet_generation_request_bridge_ready"] is True
    assert material["cr06_packet_generation_request_ref"] == cr.P7_R54_AHR_CR06_DEFAULT_PACKET_GENERATION_REQUEST_REF
    assert material["cr06_packet_generation_started_here"] is False
    assert material["cr06_body_full_packet_generation_started_here"] is False
    assert material["cr06_body_full_packet_generated_here"] is False
    assert material["cr06_body_full_packet_content_included"] is False
    assert material["cr06_local_absolute_path_included"] is False
    assert material["cr06_body_hash_included"] is False
    assert material["cr06_actual_human_review_run_here"] is False

    assert material["packet_generation_receipt_status_ref"] == cr.P7_R54_AHR_CR07_PACKET_RECEIPT_ACCEPTED_STATUS_REF
    assert material["packet_generation_receipt_ready"] is True
    assert material["packet_generation_receipt_reason_refs"] == [cr.P7_R54_AHR_CR07_READY_REASON_REF]
    assert material["packet_generation_receipt_blocker_refs"] == []
    assert material["packet_generation_receipt_input_provided"] is True
    assert material["receipt_input_forbidden_key_detected"] is False
    assert material["packet_generation_receipt_ref"] == cr.P7_R54_AHR_CR07_DEFAULT_PACKET_GENERATION_RECEIPT_REF
    assert material["packet_generation_receipt_ref_present"] is True
    assert material["packet_case_count"] == 24
    assert material["packet_case_count_matches_manifest"] is True
    assert material["packet_completeness_scan_ref"] == cr.P7_R54_AHR_CR07_DEFAULT_PACKET_COMPLETENESS_SCAN_REF
    assert material["packet_completeness_scan_ref_present"] is True
    assert material["packet_completeness_passed"] is True
    assert material["export_denylist_scan_ref"] == cr.P7_R54_AHR_CR07_DEFAULT_EXPORT_DENYLIST_SCAN_REF
    assert material["export_denylist_scan_ref_present"] is True
    assert material["export_denylist_scan_passed"] is True
    assert material["packet_completeness_scan_bodyfree_only"] is True
    assert material["export_denylist_scan_bodyfree_only"] is True
    assert material["receipt_does_not_include_packet_body"] is True
    assert material["receipt_does_not_include_local_absolute_path"] is True
    assert material["receipt_does_not_include_body_hash"] is True
    assert material["receipt_does_not_generate_packet_body_here"] is True
    assert material["receipt_does_not_execute_actual_human_review"] is True
    assert material["receipt_does_not_create_review_rows"] is True
    assert material["receipt_does_not_create_disposal_receipt"] is True
    assert material["receipt_is_bodyfree_counts_and_refs_only"] is True
    assert material["body_full_packet_content_included"] is False
    assert material["local_absolute_path_included"] is False
    assert material["body_hash_included"] is False
    assert material["terminal_output_body_included"] is False
    assert tuple(material["implemented_steps"]) == cr.P7_R54_AHR_CR07_IMPLEMENTED_STEPS
    assert tuple(material["not_yet_implemented_steps"]) == cr.P7_R54_AHR_CR07_NOT_YET_IMPLEMENTED_STEPS
    assert material["next_required_step"] == cr.P7_R54_AHR_CR08_STEP_REF
    _assert_bodyfree_no_touch(material)
    assert cr.assert_p7_r54_ahr_cr07_packet_generation_receipt_and_scan_contract(material) is True


@pytest.mark.parametrize(
    "receipt_patch,expected_blocker",
    [
        ({"packet_generation_receipt_ref": ""}, cr.P7_R54_AHR_CR07_RECEIPT_REF_MISSING_BLOCKER_REF),
        ({"packet_case_count": 23}, cr.P7_R54_AHR_CR07_PACKET_COUNT_NOT_24_BLOCKER_REF),
        ({"packet_case_count": 25}, cr.P7_R54_AHR_CR07_PACKET_COUNT_NOT_24_BLOCKER_REF),
        ({"packet_case_count": "not-an-int"}, cr.P7_R54_AHR_CR07_PACKET_COUNT_NOT_24_BLOCKER_REF),
        ({"packet_completeness_scan_ref": ""}, cr.P7_R54_AHR_CR07_COMPLETENESS_SCAN_REF_MISSING_BLOCKER_REF),
        ({"export_denylist_scan_ref": ""}, cr.P7_R54_AHR_CR07_EXPORT_DENYLIST_SCAN_REF_MISSING_BLOCKER_REF),
        ({"packet_completeness_passed": False}, cr.P7_R54_AHR_CR07_COMPLETENESS_SCAN_NOT_PASSED_BLOCKER_REF),
        ({"export_denylist_scan_passed": False}, cr.P7_R54_AHR_CR07_EXPORT_DENYLIST_SCAN_NOT_PASSED_BLOCKER_REF),
        ({"local_absolute_path": "/tmp/body-full"}, cr.P7_R54_AHR_CR07_FORBIDDEN_RECEIPT_KEY_BLOCKER_REF),
        ({"packet_content": "must not be exported"}, cr.P7_R54_AHR_CR07_FORBIDDEN_RECEIPT_KEY_BLOCKER_REF),
    ],
)
def test_cr07_blocks_when_receipt_or_scan_material_is_missing_or_unsafe(
    receipt_patch: dict[str, object], expected_blocker: str
) -> None:
    receipt_input = cr.build_p7_r54_ahr_cr07_bodyfree_receipt_input()
    receipt_input.update(receipt_patch)
    material = cr.build_p7_r54_ahr_cr07_packet_generation_receipt_and_scan(
        packet_generation_request_bridge=_cr06_ready(),
        receipt_input=receipt_input,
    )

    assert material["packet_generation_receipt_ready"] is False
    assert expected_blocker in material["packet_generation_receipt_blocker_refs"]
    assert material["packet_generation_receipt_ref_present"] is False
    assert material["packet_completeness_passed"] is False
    assert material["export_denylist_scan_passed"] is False
    assert material["body_full_packet_content_included"] is False
    assert material["local_absolute_path_included"] is False
    assert material["body_hash_included"] is False
    assert material["actual_human_review_run_here"] is False
    assert material["next_required_step"] == cr.P7_R54_AHR_CR07_DEFAULT_BLOCKED_NEXT_REQUIRED_STEP_REF
    assert cr.assert_p7_r54_ahr_cr07_packet_generation_receipt_and_scan_contract(material) is True


def test_cr07_blocks_when_cr06_request_bridge_is_not_ready() -> None:
    cr06 = cr.build_p7_r54_ahr_cr06_packet_generation_request_bridge()
    material = cr.build_p7_r54_ahr_cr07_packet_generation_receipt_and_scan(
        packet_generation_request_bridge=cr06,
        receipt_input=cr.build_p7_r54_ahr_cr07_bodyfree_receipt_input(),
    )

    assert material["cr06_packet_generation_request_bridge_ready"] is False
    assert material["packet_generation_receipt_ready"] is False
    assert cr.P7_R54_AHR_CR07_CR06_NOT_READY_BLOCKER_REF in material["packet_generation_receipt_blocker_refs"]
    assert cr.P7_R54_AHR_CR07_CR06_REQUEST_REF_MISSING_BLOCKER_REF in material[
        "packet_generation_receipt_blocker_refs"
    ]
    assert material["packet_generation_receipt_ref_present"] is False
    assert material["next_required_step"] == cr.P7_R54_AHR_CR07_DEFAULT_BLOCKED_NEXT_REQUIRED_STEP_REF
    assert cr.assert_p7_r54_ahr_cr07_packet_generation_receipt_and_scan_contract(material) is True


@pytest.mark.parametrize(
    "key,value",
    [
        ("cr06_schema_version", "changed"),
        ("cr06_next_required_step", "not_cr07"),
        ("cr06_packet_generation_request_bridge_ready", False),
        ("cr06_packet_generation_request_ref_present", False),
        ("cr06_packet_generation_allowed_by_preflight", False),
        ("cr06_packet_generation_started_here", True),
        ("cr06_body_full_packet_generation_started_here", True),
        ("cr06_body_full_packet_generated_here", True),
        ("cr06_body_full_packet_content_included", True),
        ("cr06_local_absolute_path_included", True),
        ("cr06_body_hash_included", True),
        ("cr06_actual_human_review_run_here", True),
        ("packet_generation_receipt_allowed_status_refs", ["changed"]),
        ("packet_generation_receipt_status_ref", cr.P7_R54_AHR_CR07_PACKET_RECEIPT_BLOCKED_STATUS_REF),
        ("packet_generation_receipt_ready", False),
        ("packet_generation_receipt_reason_refs", []),
        ("packet_generation_receipt_blocker_refs", ["blocked"]),
        ("packet_generation_receipt_blocker_ref_count", 99),
        ("packet_generation_receipt_input_provided", False),
        ("receipt_input_forbidden_key_detected", True),
        ("packet_generation_receipt_ref", ""),
        ("packet_generation_receipt_ref_present", False),
        ("packet_case_count", 23),
        ("packet_case_count_matches_manifest", False),
        ("packet_completeness_scan_ref", ""),
        ("packet_completeness_scan_ref_present", False),
        ("packet_completeness_passed", False),
        ("export_denylist_scan_ref", ""),
        ("export_denylist_scan_ref_present", False),
        ("export_denylist_scan_passed", False),
        ("packet_completeness_scan_bodyfree_only", False),
        ("export_denylist_scan_bodyfree_only", False),
        ("receipt_does_not_include_packet_body", False),
        ("receipt_does_not_include_local_absolute_path", False),
        ("receipt_does_not_include_body_hash", False),
        ("receipt_does_not_generate_packet_body_here", False),
        ("receipt_does_not_execute_actual_human_review", False),
        ("receipt_does_not_create_review_rows", False),
        ("receipt_does_not_create_disposal_receipt", False),
        ("receipt_is_bodyfree_counts_and_refs_only", False),
        ("body_full_packet_content_included", True),
        ("local_absolute_path_included", True),
        ("body_hash_included", True),
        ("terminal_output_body_included", True),
        ("actual_human_review_run_here", True),
        ("actual_human_review_complete", True),
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
        ("next_required_step", "not_cr08"),
    ],
)
def test_cr07_rejects_receipt_scan_mutations_or_execution_promotion(key: str, value: object) -> None:
    mutated = deepcopy(_cr07_ready())
    mutated[key] = value
    with pytest.raises(ValueError):
        cr.assert_p7_r54_ahr_cr07_packet_generation_receipt_and_scan_contract(mutated)


def test_cr07_rejects_forbidden_body_or_question_key_in_material() -> None:
    mutated = deepcopy(_cr07_ready())
    mutated["question_text"] = "must not be exported"
    with pytest.raises(ValueError):
        cr.assert_p7_r54_ahr_cr07_packet_generation_receipt_and_scan_contract(mutated)


def test_cr06_cr07_alias_functions_match_primary_builders_and_contracts() -> None:
    cr05 = cr.build_p7_r54_ahr_current_received_actual_local_review_operation_local_only_preflight_bodyfree(
        explicit_allow_ref=cr.P7_R54_AHR_CR05_DEFAULT_EXPLICIT_ALLOW_REF,
    )
    cr06 = cr.build_p7_r54_ahr_current_received_actual_local_review_operation_packet_generation_request_bridge_bodyfree(
        local_only_preflight=cr05,
    )
    cr07 = cr.build_p7_r54_ahr_current_received_actual_local_review_operation_packet_generation_receipt_and_scan_bodyfree(
        packet_generation_request_bridge=cr06,
        receipt_input=cr.build_p7_r54_ahr_cr07_bodyfree_receipt_input(),
    )

    assert cr.assert_p7_r54_ahr_current_received_actual_local_review_operation_packet_generation_request_bridge_bodyfree_contract(cr06) is True
    assert cr.assert_p7_r54_ahr_current_received_actual_local_review_operation_packet_generation_receipt_and_scan_bodyfree_contract(cr07) is True
    assert cr06["operation_step_ref"] == cr.P7_R54_AHR_CR06_STEP_REF
    assert cr07["operation_step_ref"] == cr.P7_R54_AHR_CR07_STEP_REF
    assert cr07["next_required_step"] == cr.P7_R54_AHR_CR08_STEP_REF
