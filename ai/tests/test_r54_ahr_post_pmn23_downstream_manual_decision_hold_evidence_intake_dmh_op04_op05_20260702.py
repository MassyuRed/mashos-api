# -*- coding: utf-8 -*-
"""R54-AHR Post-PMN23 downstream manual decision hold DMH-OP04/OP05 tests."""

from __future__ import annotations

from copy import deepcopy
from pathlib import Path
import sys

import pytest

TEST_DIR = Path(__file__).resolve().parent
if str(TEST_DIR) not in sys.path:
    sys.path.insert(0, str(TEST_DIR))

import emlis_ai_p7_r54_ahr_post_pmn23_downstream_manual_decision_hold_evidence_intake_20260701 as dmh
import test_r54_ahr_post_pmn23_downstream_manual_decision_hold_evidence_intake_dmh_op02_op03_20260702 as dmh_op02_op03_prev

_READY_OP03_CACHE: dict[str, object] | None = None
_READY_OP04_CACHE: dict[str, object] | None = None
_READY_OP05_CACHE: dict[str, object] | None = None


def _ready_op03() -> dict[str, object]:
    global _READY_OP03_CACHE
    if _READY_OP03_CACHE is None:
        material = dmh_op02_op03_prev._ready_op03()
        assert dmh.assert_p7_r54_ahr_post_pmn23_dmh_op03_explicit_allow_receipt_local_only_review_session_envelope_contract(material) is True
        _READY_OP03_CACHE = material
    return deepcopy(_READY_OP03_CACHE)


def _ready_op04() -> dict[str, object]:
    global _READY_OP04_CACHE
    if _READY_OP04_CACHE is None:
        material = dmh.build_p7_r54_ahr_post_pmn23_dmh_op04_24_case_manifest_packet_request_boundary(
            explicit_allow_receipt_local_only_review_session_envelope=_ready_op03(),
        )
        assert dmh.assert_p7_r54_ahr_post_pmn23_dmh_op04_24_case_manifest_packet_request_boundary_contract(material) is True
        _READY_OP04_CACHE = material
    return deepcopy(_READY_OP04_CACHE)


def _ready_packet_generation_receipt(review_session_id: str | None = None) -> dict[str, object]:
    receipt = dmh.build_p7_r54_ahr_post_pmn23_dmh_op05_packet_generation_receipt_bodyfree(
        review_session_id=review_session_id,
    )
    assert receipt["schema_version"] == dmh.P7_R54_AHR_POST_PMN23_DMH_OP05_PACKET_GENERATION_RECEIPT_SCHEMA_VERSION
    assert receipt["body_free"] is True
    return receipt


def _ready_op05() -> dict[str, object]:
    global _READY_OP05_CACHE
    if _READY_OP05_CACHE is None:
        op04 = _ready_op04()
        receipt = _ready_packet_generation_receipt(str(op04["review_session_id"]))
        material = dmh.build_p7_r54_ahr_post_pmn23_dmh_op05_body_full_packet_generation_receipt_intake_boundary(
            twenty_four_case_manifest_packet_request_boundary=op04,
            packet_generation_receipt_bodyfree=receipt,
        )
        assert dmh.assert_p7_r54_ahr_post_pmn23_dmh_op05_body_full_packet_generation_receipt_intake_boundary_contract(material) is True
        _READY_OP05_CACHE = material
    return deepcopy(_READY_OP05_CACHE)


def _assert_bodyfree_no_touch_no_promotion(material: dict[str, object]) -> None:
    assert material["body_free"] is True
    for key in dmh.P7_R54_AHR_POST_PMN23_DMH_REQUIRED_FALSE_FLAG_REFS:
        assert material[key] is False, key
    for marker_map_key in ("public_contract", "post_pmn23_no_touch_contract", "body_free_markers"):
        assert material[marker_map_key]
        assert all(value is False for value in material[marker_map_key].values()), marker_map_key
    assert all(value is False for value in material["not_claimed_boundary"].values())
    for forbidden_key in dmh.P7_R54_AHR_POST_PMN23_DMH_FORBIDDEN_PAYLOAD_KEY_REFS:
        assert forbidden_key not in material, forbidden_key


def test_dmh_op04_fixes_24_case_manifest_and_packet_request_boundary_without_packet_generation() -> None:
    material = _ready_op04()

    assert set(material) == set(dmh.P7_R54_AHR_POST_PMN23_DMH_OP04_REQUIRED_FIELD_REFS)
    assert material["schema_version"] == dmh.P7_R54_AHR_POST_PMN23_DMH_OP04_24_CASE_MANIFEST_PACKET_REQUEST_BOUNDARY_SCHEMA_VERSION
    assert material["operation_step_ref"] == dmh.P7_R54_AHR_POST_PMN23_DMH_OP04_STEP_REF
    assert material["dmh_op04_status_ref"] == dmh.P7_R54_AHR_POST_PMN23_DMH_OP04_READY_STATUS_REF
    assert material["dmh_op04_ready"] is True
    assert material["dmh_op04_blocker_refs"] == []
    assert tuple(material["dmh_op04_reason_refs"]) == dmh.P7_R54_AHR_POST_PMN23_DMH_OP04_READY_REASON_REFS
    assert material["op03_dmh_ready"] is True
    assert material["op03_explicit_allow_receipt_present"] is True
    assert material["op03_body_full_packet_generation_allowed_by_explicit_allow_receipt"] is True
    assert material["op03_local_only_review_session_envelope_ready"] is True
    assert material["case_manifest_ref"] == dmh.P7_R54_AHR_POST_PMN23_DMH_OP04_CASE_MANIFEST_REF
    assert material["case_manifest_boundary_ready"] is True
    assert material["required_case_count"] == 24
    assert material["total_case_count"] == 24
    assert material["case_ref_id_count"] == 24
    assert material["blind_case_id_count"] == 24
    assert material["packet_ref_id_count"] == 24
    assert material["selection_row_count_required"] == 24
    assert material["sanitized_review_result_row_count_required"] == 24
    assert material["rating_row_count_required"] == 24
    assert material["question_need_observation_row_count_required"] == 24
    assert material["case_distribution"] == dmh.P7_R54_AHR_POST_PMN23_DMH_OP04_MANIFEST_DISTRIBUTION
    assert material["case_distribution_total_count"] == 24
    assert material["case_distribution_matches_design"] is True
    assert material["family_case_counts"] == dmh.P7_R54_AHR_POST_PMN23_DMH_OP04_MANIFEST_DISTRIBUTION
    assert material["low_information_boundary_case_count"] == 2
    assert material["free_tier_boundary_case_count"] == 2
    assert material["boundary_case_count"] == 4
    assert material["case_ref_ids_unique"] is True
    assert material["blind_case_ids_unique"] is True
    assert material["packet_ref_ids_unique"] is True
    assert material["blind_case_id_case_ref_separated"] is True
    assert material["blind_case_id_packet_ref_separated"] is True
    assert material["case_ref_id_packet_ref_separated"] is True
    assert material["case_manifest_row_count"] == 24
    assert material["controller_manifest_row_count"] == 24
    assert material["reviewer_facing_row_count"] == 24
    assert material["reviewer_identifier_policy_ref"] == dmh.P7_R54_AHR_POST_PMN23_DMH_OP04_REVIEWER_IDENTIFIER_POLICY_REF
    assert material["controller_keeps_family_tier_expected_refs"] is True
    assert material["reviewer_receives_blind_case_id_only"] is True
    for exposed_key in (
        "reviewer_facing_family_exposed",
        "reviewer_facing_tier_exposed",
        "reviewer_facing_case_ref_exposed",
        "reviewer_facing_packet_ref_exposed",
        "reviewer_facing_expected_result_exposed",
        "reviewer_facing_hidden_metadata_exposed",
    ):
        assert material[exposed_key] is False
    assert material["p4_r11_rows_confused_as_r54_review_rows"] is False
    assert material["p4_r11_rows_mixed_in"] is False
    assert material["p4_r11_rows_mixed_in_count"] == 0
    assert material["packet_generation_request_ref"] == dmh.P7_R54_AHR_POST_PMN23_DMH_OP04_PACKET_GENERATION_REQUEST_REF
    assert material["packet_generation_request_ready"] is True
    assert material["packet_generation_request_allowed_after_op04"] is True
    assert material["body_full_packet_generation_may_be_run_after_this_boundary_by_external_local_only_operation"] is True
    assert material["packet_generation_request_forbidden_payload_key_paths"] == []
    assert material["body_full_packet_generation_executed_here"] is False
    assert material["body_full_packet_generated_here"] is False
    assert material["body_full_packet_materialized_here"] is False
    assert material["dmh_op04_does_not_generate_body_full_packet"] is True
    assert material["dmh_op04_does_not_run_actual_human_review"] is True
    assert material["dmh_op04_does_not_create_operation_receipt_or_rows_or_disposal"] is True
    assert material["dmh_op04_does_not_start_p8_p6_r52_or_release"] is True
    assert tuple(material["implemented_steps"]) == dmh.P7_R54_AHR_POST_PMN23_DMH_OP04_IMPLEMENTED_STEPS
    assert tuple(material["not_yet_implemented_steps"]) == dmh.P7_R54_AHR_POST_PMN23_DMH_OP04_NOT_YET_IMPLEMENTED_STEPS
    assert material["next_required_step"] == dmh.P7_R54_AHR_POST_PMN23_DMH_OP05_STEP_REF
    _assert_bodyfree_no_touch_no_promotion(material)


def test_dmh_op04_packet_request_payload_is_bodyfree_and_schema_like_without_file_creation() -> None:
    material = _ready_op04()
    payload = material["packet_generation_request_payload"]

    assert tuple(payload.keys()) == dmh.P7_R54_AHR_POST_PMN23_DMH_OP04_PACKET_GENERATION_REQUEST_REQUIRED_FIELD_REFS
    assert payload["packet_generation_request_ref"] == dmh.P7_R54_AHR_POST_PMN23_DMH_OP04_PACKET_GENERATION_REQUEST_REF
    assert payload["review_session_id"] == material["review_session_id"]
    assert payload["actual_review_basis_ref"] == dmh.P7_R54_AHR_POST_PMN23_DMH_ACTUAL_REVIEW_BASIS_REF
    assert payload["required_case_count"] == 24
    assert payload["case_manifest_ref"] == dmh.P7_R54_AHR_POST_PMN23_DMH_OP04_CASE_MANIFEST_REF
    assert payload["explicit_allow_ref"] == dmh.P7_R54_AHR_POST_PMN23_DMH_OP03_EXPLICIT_ALLOW_REF
    assert payload["local_only_required"] is True
    assert payload["must_not_export"] is True
    assert payload["packet_completeness_scan_required"] is True
    assert payload["export_denylist_scan_required"] is True
    assert payload["purge_required"] is True
    assert payload["body_free"] is True
    assert material["packet_generation_request_required_field_ref_count"] == len(dmh.P7_R54_AHR_POST_PMN23_DMH_OP04_PACKET_GENERATION_REQUEST_REQUIRED_FIELD_REFS)
    for forbidden_key in dmh.P7_R54_AHR_POST_PMN23_DMH_FORBIDDEN_PAYLOAD_KEY_REFS:
        assert forbidden_key not in payload, forbidden_key


def test_dmh_op04_blocks_without_op03_and_does_not_allow_packet_request() -> None:
    material = dmh.build_p7_r54_ahr_post_pmn23_dmh_op04_24_case_manifest_packet_request_boundary()

    assert set(material) == set(dmh.P7_R54_AHR_POST_PMN23_DMH_OP04_REQUIRED_FIELD_REFS)
    assert material["dmh_op04_status_ref"] == dmh.P7_R54_AHR_POST_PMN23_DMH_OP04_BLOCKED_STATUS_REF
    assert material["dmh_op04_ready"] is False
    assert "dmh_op04_explicit_allow_local_only_review_session_envelope_missing" in material["dmh_op04_blocker_refs"]
    assert material["case_manifest_boundary_ready"] is False
    assert material["total_case_count"] == 0
    assert material["packet_generation_request_payload"] == {}
    assert material["packet_generation_request_ready"] is False
    assert material["packet_generation_request_allowed_after_op04"] is False
    assert material["body_full_packet_generation_may_be_run_after_this_boundary_by_external_local_only_operation"] is False
    assert tuple(material["implemented_steps"]) == dmh.P7_R54_AHR_POST_PMN23_DMH_OP03_IMPLEMENTED_STEPS
    assert material["next_required_step"] == dmh.P7_R54_AHR_POST_PMN23_DMH_OP04_BLOCKED_NEXT_REQUIRED_STEP_REF
    assert dmh.assert_p7_r54_ahr_post_pmn23_dmh_op04_24_case_manifest_packet_request_boundary_contract(material) is True
    _assert_bodyfree_no_touch_no_promotion(material)


@pytest.mark.parametrize(
    ("field", "bad_value"),
    [
        ("total_case_count", 23),
        ("case_ref_id_count", 23),
        ("packet_ref_id_count", 23),
        ("case_distribution_matches_design", False),
        ("case_ref_ids_unique", False),
        ("reviewer_facing_case_ref_exposed", True),
        ("packet_generation_request_ready", False),
        ("body_full_packet_generation_executed_here", True),
        ("body_full_packet_generated_here", True),
        ("body_full_packet_materialized_here", True),
        ("question_text_included", True),
        ("actual_human_review_run_here", True),
        ("p8_start_allowed", True),
        ("release_allowed", True),
    ],
)
def test_dmh_op04_contract_rejects_manifest_packet_request_body_or_promotion_mutation(field: str, bad_value: object) -> None:
    material = _ready_op04()
    mutated = deepcopy(material)
    mutated[field] = bad_value

    with pytest.raises(ValueError):
        dmh.assert_p7_r54_ahr_post_pmn23_dmh_op04_24_case_manifest_packet_request_boundary_contract(mutated)


def test_dmh_op05_packet_generation_receipt_fixture_is_bodyfree_without_body_or_path_hash() -> None:
    op04 = _ready_op04()
    receipt = _ready_packet_generation_receipt(str(op04["review_session_id"]))

    assert set(receipt) == set(dmh.P7_R54_AHR_POST_PMN23_DMH_OP05_REQUIRED_PACKET_RECEIPT_FIELD_REFS)
    assert receipt["packet_generation_receipt_ref"] == dmh.P7_R54_AHR_POST_PMN23_DMH_OP05_PACKET_GENERATION_RECEIPT_REF
    assert receipt["review_session_id"] == op04["review_session_id"]
    assert receipt["packet_generation_request_ref"] == dmh.P7_R54_AHR_POST_PMN23_DMH_OP04_PACKET_GENERATION_REQUEST_REF
    assert receipt["actual_review_basis_ref"] == dmh.P7_R54_AHR_POST_PMN23_DMH_ACTUAL_REVIEW_BASIS_REF
    assert receipt["actual_source_ref"] == dmh.P7_R54_AHR_POST_PMN23_DMH_OP05_EXPECTED_ACTUAL_SOURCE_REF
    assert receipt["packet_materialized_local_only"] is True
    assert receipt["packet_count"] == 24
    assert receipt["packet_ref_id_count"] == 24
    assert tuple(receipt["packet_ref_ids"]) == tuple(op04["packet_ref_ids"])
    assert receipt["body_full_exported"] is False
    assert receipt["body_full_packet_exported_to_artifact"] is False
    assert receipt["local_absolute_path_included"] is False
    assert receipt["body_hash_stored"] is False
    assert receipt["terminal_output_body_included"] is False
    assert receipt["packet_content_included"] is False
    assert receipt["question_text_included"] is False
    assert receipt["draft_question_text_included"] is False
    assert receipt["receipt_source_kind_ref"] == dmh.P7_R54_AHR_POST_PMN23_DMH_OP05_CONTRACT_FIXTURE_SOURCE_KIND_REF
    assert receipt["body_free"] is True
    for forbidden_key in dmh.P7_R54_AHR_POST_PMN23_DMH_FORBIDDEN_PAYLOAD_KEY_REFS:
        assert forbidden_key not in receipt, forbidden_key


def test_dmh_op05_accepts_packet_generation_receipt_intake_boundary_without_human_review_or_promotion() -> None:
    material = _ready_op05()

    assert set(material) == set(dmh.P7_R54_AHR_POST_PMN23_DMH_OP05_REQUIRED_FIELD_REFS)
    assert material["schema_version"] == dmh.P7_R54_AHR_POST_PMN23_DMH_OP05_BODY_FULL_PACKET_GENERATION_RECEIPT_INTAKE_BOUNDARY_SCHEMA_VERSION
    assert material["operation_step_ref"] == dmh.P7_R54_AHR_POST_PMN23_DMH_OP05_STEP_REF
    assert material["dmh_op05_status_ref"] == dmh.P7_R54_AHR_POST_PMN23_DMH_OP05_READY_STATUS_REF
    assert material["dmh_op05_ready"] is True
    assert material["dmh_op05_blocker_refs"] == []
    assert tuple(material["dmh_op05_reason_refs"]) == dmh.P7_R54_AHR_POST_PMN23_DMH_OP05_READY_REASON_REFS
    assert material["op04_dmh_ready"] is True
    assert material["op04_packet_generation_request_ready"] is True
    assert material["op04_case_manifest_boundary_ready"] is True
    assert material["op04_packet_generation_request_ref"] == dmh.P7_R54_AHR_POST_PMN23_DMH_OP04_PACKET_GENERATION_REQUEST_REF
    assert material["packet_generation_receipt_present"] is True
    assert material["packet_generation_receipt_schema_version"] == dmh.P7_R54_AHR_POST_PMN23_DMH_OP05_PACKET_GENERATION_RECEIPT_SCHEMA_VERSION
    assert material["packet_generation_receipt_ref"] == dmh.P7_R54_AHR_POST_PMN23_DMH_OP05_PACKET_GENERATION_RECEIPT_REF
    assert material["packet_generation_receipt_actual_source_ref_allowed"] is True
    assert material["packet_generation_receipt_source_kind_is_contract_fixture_not_real_evidence"] is True
    assert material["packet_generation_request_ref_confirmed"] is True
    assert material["actual_review_basis_ref_confirmed"] is True
    assert material["packet_materialized_local_only"] is True
    assert material["packet_count"] == 24
    assert material["packet_ref_id_count"] == 24
    assert material["packet_ref_ids_unique"] is True
    assert material["expected_packet_count"] == 24
    assert material["body_full_exported"] is False
    assert material["body_full_packet_exported_to_artifact"] is False
    assert material["local_absolute_path_included"] is False
    assert material["body_hash_stored"] is False
    assert material["terminal_output_body_included"] is False
    assert material["packet_content_included"] is False
    assert material["question_text_included"] is False
    assert material["draft_question_text_included"] is False
    assert material["packet_generation_receipt_bodyfree_only"] is True
    assert material["packet_generation_receipt_content_export_absent"] is True
    assert material["packet_generation_receipt_path_hash_terminal_output_absent"] is True
    assert material["packet_generation_receipt_intaked_here"] is True
    assert material["packet_generation_receipt_from_real_operation_claimed_here"] is False
    assert material["packet_completeness_export_denylist_scan_required_next"] is True
    assert material["actual_human_review_still_not_run"] is True
    assert material["actual_operation_receipt_still_not_received"] is True
    assert material["actual_review_rows_still_not_created"] is True
    assert material["actual_disposal_purge_still_not_run"] is True
    assert material["actual_review_evidence_complete_from_real_review_still_false"] is True
    assert material["body_full_packet_generation_executed_here"] is False
    assert material["body_full_packet_generated_here"] is False
    assert material["body_full_packet_materialized_here"] is False
    assert material["dmh_op05_does_not_generate_body_full_packet_here"] is True
    assert material["dmh_op05_does_not_run_actual_human_review"] is True
    assert material["dmh_op05_does_not_create_operation_receipt_or_rows_or_disposal"] is True
    assert material["dmh_op05_does_not_start_p8_p6_r52_or_release"] is True
    assert tuple(material["implemented_steps"]) == dmh.P7_R54_AHR_POST_PMN23_DMH_OP05_IMPLEMENTED_STEPS
    assert tuple(material["not_yet_implemented_steps"]) == dmh.P7_R54_AHR_POST_PMN23_DMH_OP05_NOT_YET_IMPLEMENTED_STEPS
    assert material["next_required_step"] == dmh.P7_R54_AHR_POST_PMN23_DMH_OP06_STEP_REF
    _assert_bodyfree_no_touch_no_promotion(material)


def test_dmh_op05_blocks_without_packet_generation_receipt_and_keeps_next_step_closed() -> None:
    material = dmh.build_p7_r54_ahr_post_pmn23_dmh_op05_body_full_packet_generation_receipt_intake_boundary(
        twenty_four_case_manifest_packet_request_boundary=_ready_op04(),
    )

    assert set(material) == set(dmh.P7_R54_AHR_POST_PMN23_DMH_OP05_REQUIRED_FIELD_REFS)
    assert material["dmh_op05_status_ref"] == dmh.P7_R54_AHR_POST_PMN23_DMH_OP05_BLOCKED_STATUS_REF
    assert material["dmh_op05_ready"] is False
    assert "dmh_op05_packet_generation_receipt_missing" in material["dmh_op05_blocker_refs"]
    assert material["packet_generation_receipt_present"] is False
    assert material["packet_generation_receipt_intake_boundary_ready"] is False
    assert material["packet_generation_receipt_intaked_here"] is False
    assert material["packet_completeness_export_denylist_scan_required_next"] is False
    assert tuple(material["implemented_steps"]) == dmh.P7_R54_AHR_POST_PMN23_DMH_OP04_IMPLEMENTED_STEPS
    assert material["next_required_step"] == dmh.P7_R54_AHR_POST_PMN23_DMH_OP05_BLOCKED_NEXT_REQUIRED_STEP_REF
    assert dmh.assert_p7_r54_ahr_post_pmn23_dmh_op05_body_full_packet_generation_receipt_intake_boundary_contract(material) is True
    _assert_bodyfree_no_touch_no_promotion(material)


def test_dmh_op05_blocks_receipt_with_forbidden_body_question_path_hash_keys() -> None:
    op04 = _ready_op04()
    receipt = _ready_packet_generation_receipt(str(op04["review_session_id"]))
    receipt["raw_input"] = "forbidden packet body must never be accepted"

    material = dmh.build_p7_r54_ahr_post_pmn23_dmh_op05_body_full_packet_generation_receipt_intake_boundary(
        twenty_four_case_manifest_packet_request_boundary=op04,
        packet_generation_receipt_bodyfree=receipt,
    )

    assert material["dmh_op05_ready"] is False
    assert "dmh_op05_packet_generation_receipt_forbidden_body_question_path_hash_key_detected" in material["dmh_op05_blocker_refs"]
    assert material["packet_generation_receipt_forbidden_payload_key_paths"] == ["packet_generation_receipt.raw_input"]
    assert material["packet_generation_receipt_forbidden_payload_key_path_count"] == 1
    assert material["packet_generation_receipt_intaked_here"] is False
    assert dmh.assert_p7_r54_ahr_post_pmn23_dmh_op05_body_full_packet_generation_receipt_intake_boundary_contract(material) is True


@pytest.mark.parametrize(
    ("receipt_field", "bad_value", "expected_blocker"),
    [
        ("packet_materialized_local_only", False, "dmh_op05_packet_generation_receipt_does_not_confirm_local_only_materialization"),
        ("packet_count", 23, "dmh_op05_packet_generation_receipt_packet_count_not_24"),
        ("packet_ref_id_count", 23, "dmh_op05_packet_generation_receipt_packet_ref_id_count_not_24"),
        ("body_full_exported", True, "dmh_op05_packet_generation_receipt_body_full_exported_not_false"),
        ("body_full_packet_exported_to_artifact", True, "dmh_op05_packet_generation_receipt_body_full_packet_exported_to_artifact_not_false"),
        ("local_absolute_path_included", True, "dmh_op05_packet_generation_receipt_local_absolute_path_included_not_false"),
        ("body_hash_stored", True, "dmh_op05_packet_generation_receipt_body_hash_stored_not_false"),
        ("terminal_output_body_included", True, "dmh_op05_packet_generation_receipt_terminal_output_body_included_not_false"),
        ("packet_content_included", True, "dmh_op05_packet_generation_receipt_packet_content_included_not_false"),
        ("question_text_included", True, "dmh_op05_packet_generation_receipt_question_text_included_not_false"),
        ("draft_question_text_included", True, "dmh_op05_packet_generation_receipt_draft_question_text_included_not_false"),
    ],
)
def test_dmh_op05_blocks_invalid_packet_generation_receipt_bodyfree_boundaries(
    receipt_field: str, bad_value: object, expected_blocker: str
) -> None:
    op04 = _ready_op04()
    receipt = _ready_packet_generation_receipt(str(op04["review_session_id"]))
    receipt[receipt_field] = bad_value

    material = dmh.build_p7_r54_ahr_post_pmn23_dmh_op05_body_full_packet_generation_receipt_intake_boundary(
        twenty_four_case_manifest_packet_request_boundary=op04,
        packet_generation_receipt_bodyfree=receipt,
    )

    assert material["dmh_op05_ready"] is False
    assert expected_blocker in material["dmh_op05_blocker_refs"]
    assert material["packet_generation_receipt_intaked_here"] is False
    assert dmh.assert_p7_r54_ahr_post_pmn23_dmh_op05_body_full_packet_generation_receipt_intake_boundary_contract(material) is True


@pytest.mark.parametrize(
    ("field", "bad_value"),
    [
        ("packet_materialized_local_only", False),
        ("packet_count", 23),
        ("packet_ref_id_count", 23),
        ("packet_ref_ids_unique", False),
        ("body_full_exported", True),
        ("local_absolute_path_included", True),
        ("body_hash_stored", True),
        ("packet_content_included", True),
        ("question_text_included", True),
        ("packet_generation_receipt_from_real_operation_claimed_here", True),
        ("body_full_packet_generation_executed_here", True),
        ("body_full_packet_generated_here", True),
        ("body_full_packet_materialized_here", True),
        ("actual_human_review_run_here", True),
        ("p8_start_allowed", True),
        ("release_allowed", True),
    ],
)
def test_dmh_op05_contract_rejects_receipt_body_path_hash_human_review_or_promotion_mutation(field: str, bad_value: object) -> None:
    material = _ready_op05()
    mutated = deepcopy(material)
    mutated[field] = bad_value

    with pytest.raises(ValueError):
        dmh.assert_p7_r54_ahr_post_pmn23_dmh_op05_body_full_packet_generation_receipt_intake_boundary_contract(mutated)


def test_dmh_op04_op05_aliases_match_primary_builders_and_contracts() -> None:
    op03 = _ready_op03()
    primary_op04 = dmh.build_p7_r54_ahr_post_pmn23_dmh_op04_24_case_manifest_packet_request_boundary(
        explicit_allow_receipt_local_only_review_session_envelope=op03,
    )
    alias_op04 = dmh.build_p7_r54_ahr_post_pmn23_downstream_manual_decision_hold_24_case_manifest_packet_request_boundary_bodyfree(
        explicit_allow_receipt_local_only_review_session_envelope=op03,
    )
    assert alias_op04 == primary_op04
    assert dmh.assert_p7_r54_ahr_post_pmn23_downstream_manual_decision_hold_24_case_manifest_packet_request_boundary_bodyfree_contract(alias_op04) is True

    primary_receipt = dmh.build_p7_r54_ahr_post_pmn23_dmh_op05_packet_generation_receipt_bodyfree(
        review_session_id=str(primary_op04["review_session_id"]),
    )
    alias_receipt = dmh.build_p7_r54_ahr_post_pmn23_downstream_manual_decision_hold_packet_generation_receipt_bodyfree(
        review_session_id=str(primary_op04["review_session_id"]),
    )
    assert alias_receipt == primary_receipt

    primary_op05 = dmh.build_p7_r54_ahr_post_pmn23_dmh_op05_body_full_packet_generation_receipt_intake_boundary(
        twenty_four_case_manifest_packet_request_boundary=primary_op04,
        packet_generation_receipt_bodyfree=primary_receipt,
    )
    alias_op05 = dmh.build_p7_r54_ahr_post_pmn23_downstream_manual_decision_hold_body_full_packet_generation_receipt_intake_boundary_bodyfree(
        twenty_four_case_manifest_packet_request_boundary=primary_op04,
        packet_generation_receipt_bodyfree=primary_receipt,
    )
    assert alias_op05 == primary_op05
    assert dmh.assert_p7_r54_ahr_post_pmn23_downstream_manual_decision_hold_body_full_packet_generation_receipt_intake_boundary_bodyfree_contract(alias_op05) is True
