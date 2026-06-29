# -*- coding: utf-8 -*-
"""R54-AHR-CS06/CS07 current snapshot actual review re-entry contract tests."""

from __future__ import annotations

from copy import deepcopy
from typing import Any

import pytest

import emlis_ai_p7_r54_ahr_current_snapshot_actual_review_reentry_20260628 as cs


FORBIDDEN_BODY_OR_QUESTION_KEYS = (
    "raw_input",
    "raw_body",
    "returned_emlis_body",
    "history_surface",
    "comment_text",
    "comment_text_body",
    "reviewer_free_text",
    "reviewer_note",
    "reviewer_notes",
    "reviewer_notes_body",
    "question_text",
    "draft_question_text",
    "raw_question_answer",
    "body_full_packet_content",
    "packet_content",
    "local_absolute_path",
    "local_file_path",
    "body_hash",
    "terminal_output_body",
    "stdout_body",
    "stderr_body",
    "traceback_body",
)


def _assert_bodyfree_no_touch(material: dict[str, Any]) -> None:
    assert material["body_free"] is True
    for key in cs.P7_R54_AHR_CS_FALSE_FLAG_REFS:
        assert material[key] is False, key
    for flag_map_key in ("public_contract", "r54_ahr_cs_no_touch_contract", "body_free_markers"):
        assert material[flag_map_key]
        assert all(value is False for value in material[flag_map_key].values()), flag_map_key
    for forbidden_key in FORBIDDEN_BODY_OR_QUESTION_KEYS:
        assert forbidden_key not in material


def _build_ready_cs05() -> dict[str, Any]:
    cs04 = cs.build_p7_r54_ahr_cs04_current_24_case_manifest_refreeze()
    assert cs.assert_p7_r54_ahr_cs04_current_24_case_manifest_refreeze_contract(cs04) is True
    cs05 = cs.build_p7_r54_ahr_cs05_local_only_preflight(current_24_case_manifest_refreeze=cs04)
    assert cs.assert_p7_r54_ahr_cs05_local_only_preflight_contract(cs05) is True
    return cs05


def test_cs00_to_cs05_are_present_before_cs06_cs07() -> None:
    cs00 = cs.build_p7_r54_ahr_cs00_scope_no_touch_boundary_freeze()
    cs01 = cs.build_p7_r54_ahr_cs01_current_snapshot_basis_refreeze(scope_no_touch_boundary_freeze=cs00)
    cs02 = cs.build_p7_r54_ahr_cs02_historical_helper_refs_reconcile(current_snapshot_basis_refreeze=cs01)
    cs03 = cs.build_p7_r54_ahr_cs03_manifest_packet_evidence_impact_assessment(
        historical_helper_refs_reconcile=cs02
    )
    cs04 = cs.build_p7_r54_ahr_cs04_current_24_case_manifest_refreeze(
        manifest_packet_evidence_impact_assessment=cs03
    )
    cs05 = cs.build_p7_r54_ahr_cs05_local_only_preflight(current_24_case_manifest_refreeze=cs04)

    assert cs.assert_p7_r54_ahr_cs00_scope_no_touch_boundary_freeze_contract(cs00) is True
    assert cs.assert_p7_r54_ahr_cs01_current_snapshot_basis_refreeze_contract(cs01) is True
    assert cs.assert_p7_r54_ahr_cs02_historical_helper_refs_reconcile_contract(cs02) is True
    assert cs.assert_p7_r54_ahr_cs03_manifest_packet_evidence_impact_assessment_contract(cs03) is True
    assert cs.assert_p7_r54_ahr_cs04_current_24_case_manifest_refreeze_contract(cs04) is True
    assert cs.assert_p7_r54_ahr_cs05_local_only_preflight_contract(cs05) is True
    assert tuple(cs05["implemented_steps"]) == cs.P7_R54_AHR_CS05_IMPLEMENTED_STEPS
    assert tuple(cs05["not_yet_implemented_steps"]) == cs.P7_R54_AHR_CS05_NOT_YET_IMPLEMENTED_STEPS
    assert cs05["next_required_step"] == cs.P7_R54_AHR_CS06_STEP_REF
    assert cs05["body_full_packet_generation_request_allowed_next"] is True
    assert cs05["body_full_packet_generation_performed_here"] is False


def test_cs06_packet_generation_request_receipt_bridge_ready_bodyfree() -> None:
    cs05 = _build_ready_cs05()
    material = cs.build_p7_r54_ahr_cs06_packet_generation_request_receipt_bridge(local_only_preflight=cs05)

    assert set(material) == set(cs.P7_R54_AHR_CS06_PACKET_GENERATION_REQUEST_RECEIPT_BRIDGE_REQUIRED_FIELD_REFS)
    assert material["schema_version"] == cs.P7_R54_AHR_CS06_PACKET_GENERATION_REQUEST_RECEIPT_BRIDGE_SCHEMA_VERSION
    assert material["policy_section"] == cs.P7_R54_AHR_CS06_STEP_REF
    assert material["operation_step_ref"] == cs.P7_R54_AHR_CS06_STEP_REF
    assert material["cs05_schema_version"] == cs.P7_R54_AHR_CS05_LOCAL_ONLY_PREFLIGHT_SCHEMA_VERSION
    assert material["cs05_next_required_step"] == cs.P7_R54_AHR_CS06_STEP_REF
    assert material["cs05_local_only_preflight_ready"] is True
    assert material["cs05_body_full_packet_generation_request_allowed_next"] is True

    assert material["current_basis_ref"] == cs.P7_R54_AHR_CS_ACTUAL_REVIEW_BASIS_REF
    assert material["historical_basis_ref"] == cs.P7_R54_AHR_CS_EXISTING_AHR_BASIS_REF
    assert material["actual_review_basis_ref"] == "current_received_snapshot_262_84_257_170"
    assert material["existing_ahr_basis_ref"] == "current_received_snapshot_260_83_256_169"
    assert material["existing_ahr_can_be_used_as_current_actual_review_evidence"] is False

    assert material["packet_generation_bridge_status_ref"] == cs.P7_R54_AHR_CS06_BRIDGE_READY_STATUS_REF
    assert material["packet_generation_bridge_reason_refs"] == [cs.P7_R54_AHR_CS06_READY_REASON_REF]
    assert material["execution_blocker_ids"] == []
    assert material["open_execution_blocker_ids"] == []
    assert material["request_ready_for_bridge"] is True
    assert material["current_manifest_ready_for_packet_generation_request"] is True
    assert material["local_only_preflight_ready_for_packet_generation_request"] is True
    assert material["packet_generation_request_ref"] == cs.P7_R54_AHR_CS06_PACKET_GENERATION_REQUEST_REF
    assert material["packet_generation_request_ref_present"] is True
    assert material["packet_generation_request_is_ref_only"] is True
    assert material["packet_generation_request_status_ref"] == cs.P7_R54_AHR_CS06_REQUEST_STATUS_READY_REF
    assert material["local_packet_generation_operation_ref"] == cs.P7_R54_AHR_CS06_LOCAL_PACKET_GENERATION_OPERATION_REF
    assert material["local_packet_generation_operation_ref_only"] is True
    assert material["packet_generation_receipt_status_ref"] == cs.P7_R54_AHR_CS06_RECEIPT_STATUS_READY_REF

    assert material["required_case_count"] == 24
    assert material["expected_generated_case_count"] == 24
    assert material["expected_generated_packet_count"] == 24
    assert material["generated_case_count"] == 24
    assert material["generated_packet_count"] == 24
    assert material["generated_counts_match_expected"] is True
    assert material["generated_packet_refs_match_expected_count"] is True
    assert material["case_ref_id_count"] == 24
    assert material["blind_case_id_count"] == 24
    assert material["packet_ref_id_count"] == 24
    assert len(material["case_ref_ids"]) == 24
    assert len(material["blind_case_ids"]) == 24
    assert len(material["packet_ref_ids"]) == 24
    assert material["packet_ref_ids_unique"] is True

    assert material["local_only"] is True
    assert material["must_not_export"] is True
    assert material["exported"] is False
    assert material["local_packet_exported"] is False
    assert material["content_included"] is False
    assert material["absolute_path_included"] is False
    assert material["hash_included"] is False
    assert material["terminal_output_included"] is False
    assert material["packet_generation_request_bodyfree_evidence_recorded"] is True
    assert material["packet_generation_requested_as_bodyfree_evidence_only"] is True
    assert material["packet_generation_request_does_not_include_packet_content"] is True
    assert material["local_packet_generation_operation_receipt_required"] is True
    assert material["local_packet_generation_operation_receipt_intaken"] is True
    assert material["packet_generation_receipt_intaken"] is True
    assert material["packet_generation_operation_receipt_only"] is True
    assert material["body_full_packet_generation_request_allowed_next"] is False
    assert material["body_full_generation_requested_here"] is False
    assert material["body_full_packet_generated_here"] is False
    assert material["body_full_packet_generation_performed_here"] is False
    assert material["body_full_packet_materialized_here"] is False
    assert material["body_full_packet_content_included"] is False
    assert material["packet_completeness_export_denylist_scan_allowed_next"] is True
    assert material["actual_review_execution_allowed_next"] is False
    assert material["actual_review_execution_blocked_until_packet_completeness_scan"] is True
    assert material["actual_human_review_operation_run"] is False
    assert material["actual_human_review_complete"] is False
    assert material["actual_review_evidence_complete"] is False
    assert material["p5_confirmed_final"] is False
    assert material["p6_start_allowed"] is False
    assert material["p8_start_allowed"] is False
    assert material["release_allowed"] is False
    assert tuple(material["implemented_steps"]) == cs.P7_R54_AHR_CS06_IMPLEMENTED_STEPS
    assert tuple(material["not_yet_implemented_steps"]) == cs.P7_R54_AHR_CS06_NOT_YET_IMPLEMENTED_STEPS
    assert material["next_required_step"] == cs.P7_R54_AHR_CS07_STEP_REF
    _assert_bodyfree_no_touch(material)
    assert cs.assert_p7_r54_ahr_cs06_packet_generation_request_receipt_bridge_contract(material) is True


def test_cs07_packet_completeness_export_denylist_scan_ready_bodyfree() -> None:
    cs06 = cs.build_p7_r54_ahr_cs06_packet_generation_request_receipt_bridge()
    material = cs.build_p7_r54_ahr_cs07_packet_completeness_export_denylist_scan(
        packet_generation_request_receipt_bridge=cs06
    )

    assert set(material) == set(cs.P7_R54_AHR_CS07_PACKET_COMPLETENESS_EXPORT_DENYLIST_SCAN_REQUIRED_FIELD_REFS)
    assert material["schema_version"] == cs.P7_R54_AHR_CS07_PACKET_COMPLETENESS_EXPORT_DENYLIST_SCAN_SCHEMA_VERSION
    assert material["policy_section"] == cs.P7_R54_AHR_CS07_STEP_REF
    assert material["operation_step_ref"] == cs.P7_R54_AHR_CS07_STEP_REF
    assert material["cs06_schema_version"] == cs.P7_R54_AHR_CS06_PACKET_GENERATION_REQUEST_RECEIPT_BRIDGE_SCHEMA_VERSION
    assert material["cs06_next_required_step"] == cs.P7_R54_AHR_CS07_STEP_REF
    assert material["cs06_packet_generation_bridge_status_ref"] == cs.P7_R54_AHR_CS06_BRIDGE_READY_STATUS_REF
    assert material["cs06_packet_generation_receipt_intaken"] is True
    assert material["cs06_packet_completeness_export_denylist_scan_allowed_next"] is True
    assert material["receipt_ready_for_packet_scan"] is True

    assert material["scan_status_ref"] == cs.P7_R54_AHR_CS07_SCAN_PASSED_STATUS_REF
    assert material["scan_reason_refs"] == [cs.P7_R54_AHR_CS07_READY_REASON_REF]
    assert material["execution_blocker_ids"] == []
    assert material["open_execution_blocker_ids"] == []
    assert material["required_case_count"] == 24
    assert material["expected_packet_count"] == 24
    assert material["scanned_case_count"] == 24
    assert material["scanned_packet_count"] == 24
    assert material["scanned_packet_ref_id_count"] == 24
    assert len(material["scanned_packet_ref_ids"]) == 24
    assert material["scanned_packet_refs_unique"] is True
    assert material["packet_count_complete"] is True
    assert material["packet_completeness_passed"] is True
    assert material["packet_completeness_bodyfree_only"] is True

    assert material["local_only"] is True
    assert material["must_not_export"] is True
    assert material["exported"] is False
    assert material["local_packet_exported"] is False
    assert tuple(material["export_denylist_scan_target_refs"]) == cs.P7_R54_AHR_CS07_SCAN_TARGET_REFS
    assert material["export_denylist_scan_target_count"] == len(cs.P7_R54_AHR_CS07_SCAN_TARGET_REFS)
    assert tuple(material["export_denylist_refs"]) == cs.P7_R54_AHR_CS05_EXPORT_DENYLIST_REFS
    assert material["export_denylist_ref_count"] == len(cs.P7_R54_AHR_CS05_EXPORT_DENYLIST_REFS)
    assert material["export_denylist_scan_passed"] is True
    assert tuple(material["forbidden_output_refs"]) == cs.P7_R54_AHR_CS05_FORBIDDEN_OUTPUT_REFS
    assert material["forbidden_output_ref_count"] == len(cs.P7_R54_AHR_CS05_FORBIDDEN_OUTPUT_REFS)
    assert material["forbidden_key_findings"] == []
    assert material["forbidden_key_findings_count"] == 0
    assert material["forbidden_export_flag_count"] == 0
    assert material["forbidden_key_scan_passed"] is True
    assert material["packet_completeness_export_denylist_scan_completed"] is True
    assert material["packet_completeness_export_denylist_scan_passed"] is True
    assert material["packet_completeness_export_denylist_scan_bodyfree_evidence_only"] is True
    assert material["packet_content_not_included_in_scan_evidence"] is True
    assert material["local_absolute_path_not_included_in_scan_evidence"] is True
    assert material["body_hash_not_included_in_scan_evidence"] is True
    assert material["terminal_output_not_included_in_scan_evidence"] is True
    assert material["reviewer_selection_form_freeze_allowed_next"] is True
    assert material["actual_review_execution_allowed_next"] is False
    assert material["actual_review_execution_blocked_until_reviewer_selection_form"] is True
    assert material["actual_human_review_operation_run"] is False
    assert material["actual_human_review_complete"] is False
    assert material["actual_review_evidence_complete"] is False
    assert material["p5_confirmed_final"] is False
    assert material["p6_start_allowed"] is False
    assert material["p8_start_allowed"] is False
    assert material["release_allowed"] is False
    assert tuple(material["implemented_steps"]) == cs.P7_R54_AHR_CS07_IMPLEMENTED_STEPS
    assert tuple(material["not_yet_implemented_steps"]) == cs.P7_R54_AHR_CS07_NOT_YET_IMPLEMENTED_STEPS
    assert material["next_required_step"] == cs.P7_R54_AHR_CS08_STEP_REF
    _assert_bodyfree_no_touch(material)
    assert cs.assert_p7_r54_ahr_cs07_packet_completeness_export_denylist_scan_contract(material) is True


def test_cs06_rejects_mutated_cs05_preflight_before_bridge_materialization() -> None:
    cs05 = _build_ready_cs05()
    blocked_cs05 = deepcopy(cs05)
    blocked_cs05["local_only_preflight_ready"] = False
    blocked_cs05["body_full_packet_generation_request_allowed_next"] = False

    with pytest.raises(ValueError):
        cs.build_p7_r54_ahr_cs06_packet_generation_request_receipt_bridge(local_only_preflight=blocked_cs05)


@pytest.mark.parametrize(
    "kwargs,expected_blocker",
    [
        ({"generated_case_count": 23}, "generated_case_count_not_24"),
        ({"generated_packet_count": 23}, "generated_packet_count_not_24"),
        ({"packet_generation_request_ref": "unexpected_request_ref"}, "packet_generation_request_ref_missing_or_unexpected"),
        ({"local_packet_generation_operation_ref": "unexpected_operation_ref"}, "local_packet_generation_operation_ref_missing_or_unexpected"),
        ({"exported": True}, "receipt_marked_exported"),
        ({"local_packet_exported": True}, "local_packet_exported"),
        ({"content_included": True}, "packet_content_included"),
        ({"absolute_path_included": True}, "absolute_path_included"),
        ({"hash_included": True}, "body_hash_included"),
        ({"terminal_output_included": True}, "terminal_output_body_included"),
    ],
)
def test_cs06_blocks_on_packet_generation_request_receipt_bridge_input_violations(
    kwargs: dict[str, object], expected_blocker: str
) -> None:
    material = cs.build_p7_r54_ahr_cs06_packet_generation_request_receipt_bridge(**kwargs)

    assert material["packet_generation_bridge_status_ref"] == cs.P7_R54_AHR_CS06_BRIDGE_BLOCKED_STATUS_REF
    assert expected_blocker in material["execution_blocker_ids"]
    assert material["packet_generation_request_bodyfree_evidence_recorded"] is False
    assert material["packet_generation_receipt_intaken"] is False
    assert material["packet_completeness_export_denylist_scan_allowed_next"] is False
    assert material["next_required_step"] == cs.P7_R54_AHR_CS06_BLOCKED_NEXT_REQUIRED_STEP_REF
    _assert_bodyfree_no_touch(material)
    assert cs.assert_p7_r54_ahr_cs06_packet_generation_request_receipt_bridge_contract(material) is True


def test_cs07_blocks_when_cs06_receipt_bridge_is_not_ready() -> None:
    cs06 = cs.build_p7_r54_ahr_cs06_packet_generation_request_receipt_bridge(generated_case_count=23)
    material = cs.build_p7_r54_ahr_cs07_packet_completeness_export_denylist_scan(
        packet_generation_request_receipt_bridge=cs06
    )

    assert material["scan_status_ref"] == cs.P7_R54_AHR_CS07_SCAN_BLOCKED_STATUS_REF
    assert "cs06_packet_generation_receipt_not_ready" in material["execution_blocker_ids"]
    assert material["packet_completeness_export_denylist_scan_passed"] is False
    assert material["reviewer_selection_form_freeze_allowed_next"] is False
    assert material["next_required_step"] == cs.P7_R54_AHR_CS07_BLOCKED_NEXT_REQUIRED_STEP_REF
    _assert_bodyfree_no_touch(material)
    assert cs.assert_p7_r54_ahr_cs07_packet_completeness_export_denylist_scan_contract(material) is True


def test_cs07_blocks_on_bodyfree_forbidden_findings_without_body_payload() -> None:
    material = cs.build_p7_r54_ahr_cs07_packet_completeness_export_denylist_scan(
        forbidden_key_findings=("question_text_detected_ref", "body_hash_detected_ref")
    )

    assert material["scan_status_ref"] == cs.P7_R54_AHR_CS07_SCAN_BLOCKED_STATUS_REF
    assert material["forbidden_key_findings"] == ["question_text_detected_ref", "body_hash_detected_ref"]
    assert material["forbidden_key_findings_count"] == 2
    assert material["forbidden_export_flag_count"] == 0
    assert material["packet_completeness_export_denylist_scan_passed"] is False
    assert material["reviewer_selection_form_freeze_allowed_next"] is False
    assert material["next_required_step"] == cs.P7_R54_AHR_CS07_BLOCKED_NEXT_REQUIRED_STEP_REF
    assert "question_text_detected_ref" in material["execution_blocker_ids"]
    assert "body_hash_detected_ref" in material["execution_blocker_ids"]
    _assert_bodyfree_no_touch(material)
    assert cs.assert_p7_r54_ahr_cs07_packet_completeness_export_denylist_scan_contract(material) is True


@pytest.mark.parametrize(
    "kwargs,expected_blocker",
    [
        ({"scanned_case_count": 23}, "scanned_case_count_not_24"),
        ({"scanned_packet_count": 23}, "scanned_packet_count_not_24"),
        ({"exported": True}, "exported_flag_present"),
        ({"local_packet_exported": True}, "local_packet_exported"),
        ({"forbidden_key_findings": ["packet_content_included"]}, "packet_content_included"),
        ({"forbidden_key_findings": ["local_absolute_path_included"]}, "local_absolute_path_included"),
        ({"forbidden_key_findings": ["body_hash_included"]}, "body_hash_included"),
        ({"forbidden_key_findings": ["terminal_output_body_included"]}, "terminal_output_body_included"),
    ],
)
def test_cs07_blocks_on_packet_completeness_or_export_denylist_input_violations(
    kwargs: dict[str, object], expected_blocker: str
) -> None:
    material = cs.build_p7_r54_ahr_cs07_packet_completeness_export_denylist_scan(**kwargs)

    assert material["scan_status_ref"] == cs.P7_R54_AHR_CS07_SCAN_BLOCKED_STATUS_REF
    assert expected_blocker in material["execution_blocker_ids"]
    assert material["packet_completeness_export_denylist_scan_passed"] is False
    assert material["reviewer_selection_form_freeze_allowed_next"] is False
    assert material["next_required_step"] == cs.P7_R54_AHR_CS07_BLOCKED_NEXT_REQUIRED_STEP_REF
    _assert_bodyfree_no_touch(material)
    assert cs.assert_p7_r54_ahr_cs07_packet_completeness_export_denylist_scan_contract(material) is True


@pytest.mark.parametrize(
    "key,value",
    [
        ("packet_generation_bridge_status_ref", cs.P7_R54_AHR_CS06_BRIDGE_BLOCKED_STATUS_REF),
        ("packet_generation_bridge_reason_refs", []),
        ("request_ready_for_bridge", False),
        ("packet_generation_request_ref", "unexpected_request_ref"),
        ("local_packet_generation_operation_ref", "unexpected_operation_ref"),
        ("packet_generation_request_status_ref", "unexpected_status"),
        ("packet_generation_receipt_status_ref", "unexpected_status"),
        ("generated_case_count", 23),
        ("generated_packet_count", 23),
        ("generated_counts_match_expected", False),
        ("packet_ref_id_count", 23),
        ("packet_ref_ids_unique", False),
        ("packet_generation_request_bodyfree_evidence_recorded", False),
        ("packet_generation_receipt_intaken", False),
        ("packet_completeness_export_denylist_scan_allowed_next", False),
        ("body_full_generation_requested_here", True),
        ("body_full_packet_generated_here", True),
        ("body_full_packet_generation_performed_here", True),
        ("body_full_packet_materialized_here", True),
        ("body_full_packet_content_included", True),
        ("actual_human_review_operation_run", True),
        ("actual_human_review_complete", True),
        ("actual_review_evidence_complete", True),
        ("p8_start_allowed", True),
        ("release_allowed", True),
    ],
)
def test_cs06_rejects_request_receipt_or_promotion_mutations(key: str, value: object) -> None:
    mutated = deepcopy(cs.build_p7_r54_ahr_cs06_packet_generation_request_receipt_bridge())
    mutated[key] = value
    with pytest.raises(ValueError):
        cs.assert_p7_r54_ahr_cs06_packet_generation_request_receipt_bridge_contract(mutated)


def test_cs06_rejects_duplicate_packet_refs() -> None:
    mutated = deepcopy(cs.build_p7_r54_ahr_cs06_packet_generation_request_receipt_bridge())
    mutated["packet_ref_ids"][0] = mutated["packet_ref_ids"][1]
    with pytest.raises(ValueError):
        cs.assert_p7_r54_ahr_cs06_packet_generation_request_receipt_bridge_contract(mutated)


@pytest.mark.parametrize(
    "key,value",
    [
        ("scan_status_ref", cs.P7_R54_AHR_CS07_SCAN_BLOCKED_STATUS_REF),
        ("scan_reason_refs", []),
        ("receipt_ready_for_packet_scan", False),
        ("scanned_case_count", 23),
        ("scanned_packet_count", 23),
        ("scanned_packet_ref_id_count", 23),
        ("scanned_packet_refs_unique", False),
        ("packet_count_complete", False),
        ("packet_completeness_passed", False),
        ("export_denylist_scan_passed", False),
        ("forbidden_key_scan_passed", False),
        ("packet_completeness_export_denylist_scan_completed", False),
        ("packet_completeness_export_denylist_scan_passed", False),
        ("reviewer_selection_form_freeze_allowed_next", False),
        ("exported", True),
        ("local_packet_exported", True),
        ("packet_content_included", True),
        ("actual_review_execution_allowed_next", True),
        ("actual_human_review_operation_run", True),
        ("actual_human_review_complete", True),
        ("actual_review_evidence_complete", True),
        ("p6_start_allowed", True),
        ("p8_start_allowed", True),
        ("release_allowed", True),
    ],
)
def test_cs07_rejects_scan_or_promotion_mutations(key: str, value: object) -> None:
    mutated = deepcopy(cs.build_p7_r54_ahr_cs07_packet_completeness_export_denylist_scan())
    mutated[key] = value
    with pytest.raises(ValueError):
        cs.assert_p7_r54_ahr_cs07_packet_completeness_export_denylist_scan_contract(mutated)


def test_cs07_rejects_duplicate_scanned_packet_refs() -> None:
    mutated = deepcopy(cs.build_p7_r54_ahr_cs07_packet_completeness_export_denylist_scan())
    mutated["scanned_packet_ref_ids"][0] = mutated["scanned_packet_ref_ids"][1]
    with pytest.raises(ValueError):
        cs.assert_p7_r54_ahr_cs07_packet_completeness_export_denylist_scan_contract(mutated)


def test_cs06_cs07_reject_body_question_path_or_hash_payload_keys() -> None:
    cs06 = cs.build_p7_r54_ahr_cs06_packet_generation_request_receipt_bridge()
    mutated06 = deepcopy(cs06)
    mutated06["question_text"] = "forbidden"
    with pytest.raises(ValueError):
        cs.assert_p7_r54_ahr_cs06_packet_generation_request_receipt_bridge_contract(mutated06)

    cs07 = cs.build_p7_r54_ahr_cs07_packet_completeness_export_denylist_scan()
    mutated07 = deepcopy(cs07)
    mutated07["local_absolute_path"] = "/forbidden/path"
    with pytest.raises(ValueError):
        cs.assert_p7_r54_ahr_cs07_packet_completeness_export_denylist_scan_contract(mutated07)


def test_cs06_cs07_aliases_preserve_contract() -> None:
    cs06 = cs.build_p7_r54_ahr_current_snapshot_actual_review_reentry_packet_generation_request_receipt_bridge_bodyfree()
    assert (
        cs.assert_p7_r54_ahr_current_snapshot_actual_review_reentry_packet_generation_request_receipt_bridge_bodyfree_contract(
            cs06
        )
        is True
    )

    cs07 = cs.build_p7_r54_ahr_current_snapshot_actual_review_reentry_packet_completeness_export_denylist_scan_bodyfree(
        packet_generation_request_receipt_bridge=cs06
    )
    assert (
        cs.assert_p7_r54_ahr_current_snapshot_actual_review_reentry_packet_completeness_export_denylist_scan_bodyfree_contract(
            cs07
        )
        is True
    )

    cs06_request_alias = cs.build_p7_r54_ahr_cs06_packet_generation_request_bodyfree_evidence()
    assert cs.assert_p7_r54_ahr_cs06_packet_generation_bridge_contract(cs06_request_alias) is True

    cs06_receipt_alias = cs.build_p7_r54_ahr_cs06_local_packet_generation_receipt_intake()
    assert cs.assert_p7_r54_ahr_cs06_packet_generation_request_receipt_bridge_contract(cs06_receipt_alias) is True
