# -*- coding: utf-8 -*-
from __future__ import annotations

import json
from copy import deepcopy
from functools import lru_cache

import pytest

import emlis_ai_p7_r48_p5_human_blind_qa_actual_review_packet as r48
import emlis_ai_p7_r51_p5_human_blind_qa_actual_local_manual_run as r51

FORBIDDEN_DUMP_TOKENS = (
    '"raw_input":', '"raw_answer":', '"comment_text":', '"comment_text_body":',
    '"returned_emlis_surface":', '"bounded_owned_history_review_surface":',
    '"current_input_review_surface":', '"reviewer_free_text":', '"reviewer_note":',
    '"reviewer_notes":', '"question_text":', '"draft_question_text":', '"question_body":',
    '"local_absolute_path":', '"body_content_hash":', '"packet_content_hash":',
    '"terminal_output": "', '"stdout":', '"stderr":', '"traceback":',
)
FORBIDDEN_TRUE_TOKENS = (
    '"release_allowed": true', '"p7_complete": true', '"p8_start_allowed": true',
    '"question_api_implemented": true', '"question_db_schema_implemented": true',
    '"question_rn_ui_implemented": true', '"question_response_key_implemented": true',
    '"question_trigger_logic_implemented": true', '"actual_human_review_run_here": true',
    '"actual_manual_review_run_here": true', '"body_full_packet_generated_here": true',
    '"actual_rating_rows_materialized_here": true',
    '"actual_question_need_observation_rows_materialized_here": true',
    '"actual_disposal_receipt_materialized_here": true',
)


def _assert_body_free_no_promotion(material: dict[str, object]) -> None:
    dumped = json.dumps(material, ensure_ascii=False, sort_keys=True).lower()
    for forbidden in FORBIDDEN_DUMP_TOKENS:
        assert forbidden not in dumped
    for forbidden in FORBIDDEN_TRUE_TOKENS:
        assert forbidden not in dumped


@lru_cache(maxsize=1)
def _cached_ready_envelope() -> tuple[dict[str, object]]:
    envelope = r51.build_p7_r51_r0_r3_preflight_session_envelope_chain(
        local_review_root="/tmp/cocolon_r51_actual_local_review_root",
        explicit_allow_token=r51.P7_R51_EXPLICIT_ACTUAL_LOCAL_MANUAL_RUN_ALLOW_TOKEN_REF,
        purge_plan=r51.build_p7_r51_default_local_only_purge_plan_bodyfree(),
    )
    assert envelope["envelope_status"] == "READY_FOR_24_CASE_MANIFEST_FREEZE"
    return (envelope,)


def _ready_envelope() -> dict[str, object]:
    return deepcopy(_cached_ready_envelope()[0])


@lru_cache(maxsize=1)
def _cached_manifest() -> tuple[dict[str, object]]:
    manifest = r51.build_p7_r51_24_case_manifest_freeze_bodyfree(actual_review_session_envelope=_ready_envelope())
    assert r51.assert_p7_r51_24_case_manifest_freeze_bodyfree_contract(manifest) is True
    return (manifest,)


def _manifest() -> dict[str, object]:
    return deepcopy(_cached_manifest()[0])


@lru_cache(maxsize=1)
def _cached_request() -> tuple[dict[str, object]]:
    request = r51.build_p7_r51_local_only_body_full_packet_generation_request_bodyfree(case_manifest_freeze=_manifest())
    assert r51.assert_p7_r51_local_only_body_full_packet_generation_request_bodyfree_contract(request) is True
    return (request,)


def _request() -> dict[str, object]:
    return deepcopy(_cached_request()[0])


def test_r51_r4_freezes_24_case_manifest_bodyfree_without_review_or_packet_generation() -> None:
    manifest = _manifest()
    assert manifest["schema_version"] == r51.P7_R51_24_CASE_MANIFEST_FREEZE_SCHEMA_VERSION
    assert set(manifest) == set(r51.P7_R51_24_CASE_MANIFEST_FREEZE_REQUIRED_FIELD_REFS)
    assert manifest["policy_section"] == "R51-4_24_case_manifest_freeze"
    assert manifest["review_session_status"] == "R51_24_CASE_MANIFEST_READY"
    assert manifest["manifest_status"] == "READY_FOR_LOCAL_ONLY_PACKET_GENERATION_REQUEST"
    assert manifest["next_required_step"] == r51.P7_R51_R4_NEXT_REQUIRED_STEP_REF
    assert manifest["r48_case_matrix_schema_version"] == r48.P7_R48_P5_CASE_MATRIX_SCHEMA_VERSION
    assert manifest["case_count"] == 24
    assert len(manifest["case_rows"]) == 24
    assert len(manifest["controller_manifest_rows"]) == 24
    assert len(manifest["reviewer_facing_case_index_rows"]) == 24
    assert manifest["minimums_satisfied"] is True
    assert manifest["blind_case_ids_unique"] is True
    assert manifest["case_ref_ids_unique"] is True
    assert manifest["packet_ref_ids_unique"] is True
    assert manifest["blind_case_id_case_ref_separated"] is True
    assert manifest["body_full_packet_generated_here"] is False
    assert manifest["actual_human_review_run_here"] is False
    assert manifest["p5_actual_review_still_not_run"] is True
    assert manifest["p7_complete"] is False
    assert manifest["p8_start_allowed"] is False
    assert manifest["release_allowed"] is False
    assert tuple(manifest["implemented_steps"]) == r51.P7_R51_R4_IMPLEMENTED_STEPS
    assert tuple(manifest["not_yet_implemented_steps"]) == r51.P7_R51_R4_NOT_YET_IMPLEMENTED_STEPS
    _assert_body_free_no_promotion(manifest)


def test_r51_r4_keeps_r48_distribution_and_hides_controller_refs_from_reviewer() -> None:
    manifest = _manifest()
    expected_family_counts = {family: count for family, count, _role in r48.P7_R48_P5_FIRST_FORMAL_CASE_DISTRIBUTION}
    assert manifest["family_case_counts"] == expected_family_counts
    assert manifest["owned_history_positive_case_count"] == 20
    assert manifest["boundary_case_count"] == 4
    assert manifest["low_information_boundary_case_count"] == 2
    assert manifest["free_tier_boundary_case_count"] == 2
    assert manifest["subscription_tier_ref_counts"] == {"plus": 11, "premium": 11, "free": 2}

    controller_row = manifest["controller_manifest_rows"][0]
    reviewer_row = manifest["reviewer_facing_case_index_rows"][0]
    assert set(manifest["case_rows"][0]) == set(r48.P7_R48_P5_CASE_MATRIX_ROW_FIELD_REFS)
    assert set(controller_row) == set(r51.P7_R51_24_CASE_MANIFEST_ROW_FIELD_REFS)
    assert set(reviewer_row) == set(r51.P7_R51_REVIEWER_FACING_CASE_INDEX_ROW_FIELD_REFS)
    assert controller_row["reviewer_receives_blind_case_id"] is True
    assert controller_row["reviewer_receives_case_ref_id"] is False
    assert controller_row["reviewer_receives_family"] is False
    assert controller_row["reviewer_receives_subscription_tier"] is False
    assert controller_row["reviewer_receives_expected_result"] is False
    assert reviewer_row["case_ref_hidden"] is True
    assert reviewer_row["family_hidden"] is True
    assert reviewer_row["tier_hidden"] is True
    assert reviewer_row["expected_result_hidden"] is True
    assert reviewer_row["gate_result_hidden"] is True


def test_r51_r4_blocks_when_r3_envelope_is_blocked() -> None:
    blocked_envelope = r51.build_p7_r51_actual_review_session_envelope_bodyfree(
        local_root_explicit_allow_purge_plan_preflight=r51.build_p7_r51_local_root_explicit_allow_purge_plan_preflight()
    )
    manifest = r51.build_p7_r51_24_case_manifest_freeze_bodyfree(actual_review_session_envelope=blocked_envelope)
    assert manifest["manifest_status"] == "BLOCKED_BY_R51_3_ENVELOPE"
    assert manifest["case_count"] == 0
    assert manifest["case_rows"] == []
    assert manifest["r4_24_case_manifest_freeze_built"] is False
    assert manifest["next_required_step"] == r51.P7_R51_R4_BLOCKED_NEXT_REQUIRED_STEP_REF
    assert "r51_local_review_root_missing" in manifest["execution_blocker_ids"]
    assert manifest["body_full_packet_generated_here"] is False


def test_r51_r4_contract_rejects_reviewer_leak_or_duplicate_blind_ids() -> None:
    manifest = _manifest()
    manifest["reviewer_facing_family_exposed"] = True
    with pytest.raises(ValueError):
        r51.assert_p7_r51_24_case_manifest_freeze_bodyfree_contract(manifest)

    manifest = _manifest()
    manifest["case_rows"][1]["blind_case_id"] = manifest["case_rows"][0]["blind_case_id"]
    with pytest.raises(ValueError):
        r51.assert_p7_r51_24_case_manifest_freeze_bodyfree_contract(manifest)


def test_r51_r5_creates_request_only_without_materializing_bodyfull_packets() -> None:
    request = _request()
    assert request["schema_version"] == r51.P7_R51_LOCAL_ONLY_BODY_FULL_PACKET_GENERATION_REQUEST_SCHEMA_VERSION
    assert set(request) == set(r51.P7_R51_LOCAL_ONLY_BODY_FULL_PACKET_GENERATION_REQUEST_REQUIRED_FIELD_REFS)
    assert request["policy_section"] == "R51-5_local_only_body_full_packet_generation_request"
    assert request["review_session_status"] == "R51_BODY_FULL_PACKET_GENERATION_REQUEST_READY"
    assert request["generation_request_status"] == "READY_FOR_LOCAL_ONLY_BODY_FULL_PACKET_GENERATION"
    assert request["next_required_step"] == r51.P7_R51_R5_NEXT_REQUIRED_STEP_REF
    assert request["case_count"] == 24
    assert request["packet_generation_request_case_count"] == 24
    assert request["packet_generation_request_row_count"] == 24
    assert request["requested_packet_ref_count"] == 24
    assert len(request["packet_generation_request_rows"]) == 24
    assert request["local_root_ref"] == "external_local_review_root"
    assert request["local_only_body_full_generation_allowed"] is True
    assert request["local_only_body_full_packet_generation_request_created_here"] is True
    assert request["body_full_packet_generation_request_created_here"] is True
    assert request["body_full_packet_generated_here"] is False
    assert request["body_full_packets_created_local_only"] is False
    assert request["local_file_ops_helper_created_here"] is False
    assert request["body_full_packet_writer_created_here"] is False
    assert request["body_full_packet_local_only_schema_file_created_here"] is False
    assert request["actual_human_review_run_here"] is False
    assert request["actual_manual_review_run_here"] is False
    assert request["p7_complete"] is False
    assert request["p8_start_allowed"] is False
    assert request["release_allowed"] is False
    assert tuple(request["implemented_steps"]) == r51.P7_R51_R5_IMPLEMENTED_STEPS
    assert tuple(request["not_yet_implemented_steps"]) == r51.P7_R51_R5_NOT_YET_IMPLEMENTED_STEPS
    _assert_body_free_no_promotion(request)


def test_r51_r5_request_rows_are_descriptors_not_local_files() -> None:
    row = _request()["packet_generation_request_rows"][0]
    assert set(row) == set(r51.P7_R51_PACKET_GENERATION_REQUEST_ROW_FIELD_REFS)
    assert row["request_status_ref"] == "REQUEST_READY_NOT_GENERATED"
    assert row["packet_kind"] == r51.P7_R51_PACKET_KIND
    assert row["review_kind"] == r51.P7_R51_REVIEW_KIND
    assert row["local_only_required"] is True
    assert row["must_not_export"] is True
    assert row["disposal_required"] is True
    assert row["body_full_packet_materialized_here"] is False
    assert row["local_file_written_here"] is False
    assert row["local_absolute_path_included"] is False
    assert row["body_content_hash_stored_here"] is False
    assert row["body_free"] is True


def test_r51_r5_keeps_schema_refs_as_refs_and_no_touch_flags_closed() -> None:
    request = _request()
    assert request["body_full_reviewer_packet_local_only_schema_version_ref"] == r51.P7_R51_BODY_FULL_REVIEWER_PACKET_LOCAL_ONLY_SCHEMA_VERSION
    assert tuple(request["body_full_packet_local_only_required_field_refs"]) == r51.P7_R51_BODY_FULL_PACKET_LOCAL_ONLY_REQUIRED_FIELD_REFS
    assert tuple(request["reviewer_visible_field_refs"]) == r51.P7_R50_REVIEWER_VISIBLE_FIELD_REFS
    assert tuple(request["reviewer_hidden_field_refs"]) == r51.P7_R50_REVIEWER_HIDDEN_FIELD_REFS
    assert request["root_path_exposed"] is False
    assert request["local_absolute_path_included"] is False
    assert request["local_packet_exported_allowed"] is False
    assert request["content_hash_of_body_stored_allowed"] is False
    assert request["export_candidate_refs_stored_here"] is False
    assert request["export_candidate_body_stored_here"] is False
    assert request["question_text_created_here"] is False
    assert request["schema_files_materialized_here"] is False
    assert request["api_db_rn_response_key_changed_here"] is False
    assert request["rn_visible_contract_changed_here"] is False
    assert request["public_response_top_level_key_added_here"] is False


def test_r51_r5_blocks_when_r4_manifest_is_blocked() -> None:
    blocked_manifest = r51.build_p7_r51_24_case_manifest_freeze_bodyfree(
        actual_review_session_envelope=r51.build_p7_r51_actual_review_session_envelope_bodyfree(
            local_root_explicit_allow_purge_plan_preflight=r51.build_p7_r51_local_root_explicit_allow_purge_plan_preflight()
        )
    )
    request = r51.build_p7_r51_local_only_body_full_packet_generation_request_bodyfree(case_manifest_freeze=blocked_manifest)
    assert request["generation_request_status"] == "BLOCKED_BY_R51_4_MANIFEST"
    assert request["packet_generation_request_case_count"] == 0
    assert request["packet_generation_request_rows"] == []
    assert request["local_only_body_full_packet_generation_request_created_here"] is False
    assert request["body_full_packet_generation_request_created_here"] is False
    assert request["body_full_packet_generated_here"] is False
    assert request["next_required_step"] == r51.P7_R51_R5_BLOCKED_NEXT_REQUIRED_STEP_REF
    assert "r51_body_full_packet_generation_request_blocked" in request["execution_blocker_ids"]


@pytest.mark.parametrize(
    "key,value",
    [
        ("body_full_packet_generated_here", True),
        ("body_full_packets_created_local_only", True),
        ("local_absolute_path_included", True),
        ("content_hash_of_body_stored_allowed", True),
        ("question_text_created_here", True),
        ("actual_human_review_run_here", True),
        ("release_allowed", True),
    ],
)
def test_r51_r5_contract_rejects_generation_path_hash_question_review_or_release_claims(key: str, value: object) -> None:
    request = _request()
    request[key] = value
    with pytest.raises(ValueError):
        r51.assert_p7_r51_local_only_body_full_packet_generation_request_bodyfree_contract(request)


def test_r51_r0_to_r5_chain_returns_ready_request_without_generating_packets() -> None:
    request = r51.build_p7_r51_r0_r5_packet_generation_request_chain(
        local_review_root="/tmp/cocolon_r51_actual_local_review_root",
        explicit_allow_token=r51.P7_R51_EXPLICIT_ACTUAL_LOCAL_MANUAL_RUN_ALLOW_TOKEN_REF,
        purge_plan=r51.build_p7_r51_default_local_only_purge_plan_bodyfree(),
    )
    assert request["generation_request_status"] == "READY_FOR_LOCAL_ONLY_BODY_FULL_PACKET_GENERATION"
    assert request["packet_generation_request_row_count"] == 24
    assert request["next_required_step"] == r51.P7_R51_R5_NEXT_REQUIRED_STEP_REF
    assert request["body_full_packet_generation_request_created_here"] is True
    assert request["body_full_packet_generated_here"] is False
    assert request["actual_manual_review_run_here"] is False
    assert request["p7_complete"] is False
    assert request["p8_start_allowed"] is False
    assert request["release_allowed"] is False
