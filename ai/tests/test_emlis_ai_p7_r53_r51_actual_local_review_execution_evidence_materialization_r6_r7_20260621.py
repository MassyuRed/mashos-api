# -*- coding: utf-8 -*-
"""P7-R53 R6/R7 tests for 24-case manifest and local-only packet request."""

from __future__ import annotations

from copy import deepcopy
from functools import lru_cache
from pathlib import Path

import pytest

import emlis_ai_p7_r51_p5_human_blind_qa_actual_local_manual_run as r51
import emlis_ai_p7_r53_r51_actual_local_review_execution_evidence_materialization as r53


def _assert_body_free_no_release_or_runtime_promotion(material: dict[str, object]) -> None:
    for key in r53.P7_R53_R0_R1_FALSE_KEY_REFS:
        assert material[key] is False, key
    assert material["body_free"] is True
    assert material["git_connection_required"] is False
    assert material["git_checked"] is False
    assert material["p8_start_allowed"] is False
    assert material["p7_complete"] is False
    assert material["release_allowed"] is False
    assert material["api_db_rn_response_key_changed_here"] is False
    assert material["runtime_changed_here"] is False
    assert material["actual_human_review_run_here"] is False
    assert material["actual_manual_review_run_here"] is False
    assert material["body_full_packet_generated_here"] is False
    assert material["body_full_packets_created_local_only"] is False


def _assert_no_body_payload_key_like_values(material: dict[str, object]) -> None:
    serialized = repr(material)
    for forbidden_key_repr in (
        "'raw_input':",
        "'raw_answer':",
        "'comment_text':",
        "'body':",
        "'returned_emlis_surface':",
        "'current_input_review_surface':",
        "'bounded_owned_history_surface':",
        "'reviewer_free_text':",
        "'reviewer_notes':",
        "'question_text':",
        "'draft_question_text':",
        "'local_absolute_path':",
        "'body_content_hash':",
        "'packet_content_hash':",
    ):
        assert forbidden_key_repr not in serialized


@lru_cache(maxsize=1)
def _cached_r53_r3_green_override() -> tuple[dict[str, object]]:
    preflight = r53.build_p7_r53_validation_evidence_r49_timeout_preflight(
        validation_evidence_overrides={
            "r49_split_matrix": {
                "evidence_status_ref": "PASSED_BY_R53_CURRENT_SPLIT_EXECUTION",
                "evidence_present": True,
                "passed_count": 76,
                "test_file_refs": r53.P7_R53_R49_SPLIT_MATRIX_TEST_FILE_REFS,
                "evidence_source_ref": "R53_current_session_split_green_bodyfree_evidence",
                "claim_boundary_ref": "R49 split matrix green only; wildcard bulk green is not claimed",
            }
        }
    )
    adoption = r53.build_p7_r53_r51_r0_r1_adoption_with_current_snapshot_override(
        validation_evidence_preflight=preflight,
    )
    assert r53.assert_p7_r53_r51_r0_r1_adoption_with_current_snapshot_override_contract(adoption) is True
    return (adoption,)


def _r53_r3_green_override() -> dict[str, object]:
    return deepcopy(_cached_r53_r3_green_override()[0])


def _r53_r4_ready(tmp_path: Path) -> dict[str, object]:
    local_root = tmp_path / "r53_local_review_root"
    local_root.mkdir()
    preflight = r53.build_p7_r53_local_root_explicit_allow_purge_plan_preflight(
        current_snapshot_override_adoption=_r53_r3_green_override(),
        local_review_root=str(local_root),
        repo_roots=[str(Path.cwd())],
        export_roots=[str(tmp_path / "export_root")],
        explicit_allow_token=r51.P7_R51_EXPLICIT_ACTUAL_LOCAL_MANUAL_RUN_ALLOW_TOKEN_REF,
        purge_plan=r53.build_p7_r53_default_local_only_purge_plan_bodyfree(),
    )
    assert r53.assert_p7_r53_local_root_explicit_allow_purge_plan_preflight_contract(preflight) is True
    return preflight


def _r53_r5_ready(tmp_path: Path) -> dict[str, object]:
    envelope = r53.build_p7_r53_actual_review_session_envelope_bodyfree(
        local_root_explicit_allow_purge_plan_preflight=_r53_r4_ready(tmp_path),
    )
    assert r53.assert_p7_r53_actual_review_session_envelope_bodyfree_contract(envelope) is True
    return envelope


def _r53_r6_ready(tmp_path: Path) -> dict[str, object]:
    manifest = r53.build_p7_r53_24_case_manifest_freeze_bodyfree(
        actual_review_session_envelope=_r53_r5_ready(tmp_path),
    )
    assert r53.assert_p7_r53_24_case_manifest_freeze_bodyfree_contract(manifest) is True
    return manifest


def test_r53_r6_default_manifest_is_blocked_without_ready_session_envelope_and_does_not_expose_case_rows() -> None:
    manifest = r53.build_p7_r53_24_case_manifest_freeze_bodyfree()

    assert manifest["schema_version"] == r53.P7_R53_24_CASE_MANIFEST_FREEZE_SCHEMA_VERSION
    assert set(manifest) == set(r53.P7_R53_24_CASE_MANIFEST_FREEZE_REQUIRED_FIELD_REFS)
    assert manifest["phase"].startswith("P7_")
    assert manifest["step"] == r53.P7_R53_STEP
    assert manifest["scope"] == r53.P7_R53_SCOPE
    assert manifest["policy_section"] == "R53-6_24_case_manifest_freeze"
    assert manifest["current_received_snapshot_refs"] == r53.P7_R53_CURRENT_RECEIVED_SNAPSHOT_REFS
    assert manifest["r5_envelope_ready_for_manifest"] is False
    assert manifest["manifest_status"] == "BLOCKED_BY_R53_5_ENVELOPE"
    assert manifest["review_session_status"] == "PRECHECK_BLOCKED"
    assert manifest["case_count"] == 0
    assert manifest["case_rows"] == []
    assert manifest["controller_manifest_rows"] == []
    assert manifest["reviewer_facing_case_index_rows"] == []
    assert manifest["family_case_counts"] == {}
    assert manifest["case_role_counts"] == {}
    assert manifest["subscription_tier_ref_counts"] == {}
    assert manifest["r53_6_24_case_manifest_freeze_built"] is False
    assert manifest["body_full_packet_generated_here"] is False
    assert manifest["body_full_packets_created_local_only"] is False
    assert manifest["actual_human_review_run_here"] is False
    assert manifest["p5_actual_review_still_not_run"] is True
    assert manifest["execution_blocker_ids"]
    assert manifest["open_execution_blocker_ids"] == manifest["execution_blocker_ids"]
    assert manifest["next_required_step"] == r53.P7_R53_R6_BLOCKED_NEXT_REQUIRED_STEP_REF
    assert tuple(manifest["implemented_steps"]) == r53.P7_R53_R6_IMPLEMENTED_STEPS
    assert tuple(manifest["not_yet_implemented_steps"]) == r53.P7_R53_R6_NOT_YET_IMPLEMENTED_STEPS
    assert r51.assert_p7_r51_24_case_manifest_freeze_bodyfree_contract(manifest["r51_r4_manifest_bodyfree"]) is True

    _assert_body_free_no_release_or_runtime_promotion(manifest)
    _assert_no_body_payload_key_like_values(manifest)


def test_r53_r6_ready_manifest_freezes_24_case_controller_manifest_and_blind_reviewer_index(tmp_path: Path) -> None:
    manifest = _r53_r6_ready(tmp_path)

    assert manifest["manifest_status"] == "READY_FOR_LOCAL_ONLY_PACKET_GENERATION_REQUEST"
    assert manifest["review_session_status"] == "R53_24_CASE_MANIFEST_READY"
    assert manifest["r5_envelope_ready_for_manifest"] is True
    assert manifest["r51_r4_manifest_status"] == "READY_FOR_LOCAL_ONLY_PACKET_GENERATION_REQUEST"
    assert manifest["r51_r4_next_required_step"] == r51.P7_R51_R4_NEXT_REQUIRED_STEP_REF
    assert manifest["required_case_count"] == r51.P7_R51_REQUIRED_CASE_COUNT
    assert manifest["case_count"] == 24
    assert len(manifest["case_rows"]) == 24
    assert len(manifest["controller_manifest_rows"]) == 24
    assert len(manifest["reviewer_facing_case_index_rows"]) == 24
    assert manifest["owned_history_positive_case_count"] == 20
    assert manifest["boundary_case_count"] == 4
    assert manifest["low_information_boundary_case_count"] == 2
    assert manifest["free_tier_boundary_case_count"] == 2
    assert manifest["minimums_satisfied"] is True
    assert manifest["blind_case_ids_unique"] is True
    assert manifest["case_ref_ids_unique"] is True
    assert manifest["packet_ref_ids_unique"] is True
    assert manifest["blind_case_id_case_ref_separated"] is True
    assert manifest["reviewer_receives_blind_case_id_only"] is True
    assert manifest["controller_keeps_family_tier_expected_refs"] is True
    assert manifest["reviewer_facing_family_exposed"] is False
    assert manifest["reviewer_facing_tier_exposed"] is False
    assert manifest["reviewer_facing_expected_result_exposed"] is False
    assert manifest["execution_blocker_ids"] == []
    assert manifest["next_required_step"] == r53.P7_R53_R6_NEXT_REQUIRED_STEP_REF
    assert manifest["r53_6_24_case_manifest_freeze_built"] is True

    for row in manifest["reviewer_facing_case_index_rows"]:
        assert row["reviewer_identifier_kind"] == "blind_case_id_only"
        assert row["case_ref_hidden"] is True
        assert row["family_hidden"] is True
        assert row["tier_hidden"] is True
        assert row["expected_result_hidden"] is True
        assert "case_ref_id" not in row
        assert "family" not in row
        assert "subscription_tier_ref" not in row

    _assert_body_free_no_release_or_runtime_promotion(manifest)
    _assert_no_body_payload_key_like_values(manifest)


@pytest.mark.parametrize(
    "key,value",
    [
        ("reviewer_facing_family_exposed", True),
        ("body_full_packet_generated_here", True),
        ("body_full_packets_created_local_only", True),
        ("actual_human_review_run_here", True),
        ("p8_start_allowed", True),
        ("release_allowed", True),
        ("api_db_rn_response_key_changed_here", True),
    ],
)
def test_r53_r6_rejects_manifest_leaks_body_generation_review_or_release_promotion(
    tmp_path: Path,
    key: str,
    value: object,
) -> None:
    manifest = _r53_r6_ready(tmp_path)
    manifest[key] = value
    with pytest.raises(ValueError):
        r53.assert_p7_r53_24_case_manifest_freeze_bodyfree_contract(manifest)


def test_r53_r6_rejects_reviewer_facing_controller_identifier_leak(tmp_path: Path) -> None:
    manifest = _r53_r6_ready(tmp_path)
    manifest["reviewer_facing_case_index_rows"][0]["case_ref_id"] = manifest["case_rows"][0]["case_ref_id"]
    with pytest.raises(ValueError):
        r53.assert_p7_r53_24_case_manifest_freeze_bodyfree_contract(manifest)


def test_r53_r7_default_packet_generation_request_is_blocked_without_ready_manifest_and_writes_nothing() -> None:
    request = r53.build_p7_r53_local_only_body_full_packet_generation_request_bodyfree()

    assert request["schema_version"] == r53.P7_R53_LOCAL_ONLY_BODY_FULL_PACKET_GENERATION_REQUEST_SCHEMA_VERSION
    assert set(request) == set(r53.P7_R53_LOCAL_ONLY_BODY_FULL_PACKET_GENERATION_REQUEST_REQUIRED_FIELD_REFS)
    assert request["policy_section"] == "R53-7_local_only_body_full_packet_generation_request_optional_writer"
    assert request["current_received_snapshot_refs"] == r53.P7_R53_CURRENT_RECEIVED_SNAPSHOT_REFS
    assert request["r6_manifest_ready_for_packet_generation_request"] is False
    assert request["generation_request_status"] == "BLOCKED_BY_R53_6_MANIFEST"
    assert request["review_session_status"] == "PRECHECK_BLOCKED"
    assert request["packet_generation_request_row_count"] == 0
    assert request["packet_generation_request_rows"] == []
    assert request["local_only_body_full_packet_generation_request_created_here"] is False
    assert request["body_full_packet_generation_request_created_here"] is False
    assert request["optional_writer_boundary_materialized_here"] is True
    assert request["optional_writer_execution_supported_later"] is False
    assert request["optional_writer_executed_here"] is False
    assert request["optional_writer_public_runtime_callable"] is False
    assert request["optional_writer_requires_explicit_allow_local_root_purge_plan"] is True
    assert request["optional_writer_result_bodyfree_only"] is True
    assert request["local_absolute_path_included"] is False
    assert request["body_full_packet_generated_here"] is False
    assert request["body_full_packets_created_local_only"] is False
    assert request["actual_human_review_run_here"] is False
    assert request["r53_7_local_only_body_full_packet_generation_request_built"] is False
    assert request["next_required_step"] == r53.P7_R53_R7_BLOCKED_NEXT_REQUIRED_STEP_REF
    assert tuple(request["implemented_steps"]) == r53.P7_R53_R7_IMPLEMENTED_STEPS
    assert tuple(request["not_yet_implemented_steps"]) == r53.P7_R53_R7_NOT_YET_IMPLEMENTED_STEPS
    assert r51.assert_p7_r51_local_only_body_full_packet_generation_request_bodyfree_contract(
        request["r51_r5_generation_request_bodyfree"]
    ) is True

    _assert_body_free_no_release_or_runtime_promotion(request)
    _assert_no_body_payload_key_like_values(request)


def test_r53_r7_ready_packet_generation_request_creates_24_bodyfree_request_rows_and_optional_writer_boundary_only(
    tmp_path: Path,
) -> None:
    request = r53.build_p7_r53_local_only_body_full_packet_generation_request_bodyfree(
        case_manifest_freeze=_r53_r6_ready(tmp_path),
    )

    assert request["generation_request_status"] == "READY_FOR_LOCAL_ONLY_BODY_FULL_PACKET_GENERATION"
    assert request["review_session_status"] == "R53_BODY_FULL_PACKET_GENERATION_REQUEST_READY"
    assert request["r6_manifest_ready_for_packet_generation_request"] is True
    assert request["r51_r5_generation_request_status"] == "READY_FOR_LOCAL_ONLY_BODY_FULL_PACKET_GENERATION"
    assert request["r51_r5_next_required_step"] == r51.P7_R51_R5_NEXT_REQUIRED_STEP_REF
    assert request["required_case_count"] == r51.P7_R51_REQUIRED_CASE_COUNT
    assert request["case_count"] == 24
    assert request["packet_generation_request_case_count"] == 24
    assert request["packet_generation_request_row_count"] == 24
    assert len(request["packet_generation_request_rows"]) == 24
    assert request["requested_packet_ref_count"] == 24
    assert request["blind_case_id_count"] == 24
    assert request["packet_ref_ids_unique"] is True
    assert request["case_ref_ids_unique"] is True
    assert request["body_full_reviewer_packet_local_only_schema_version_ref"] == r51.P7_R51_BODY_FULL_REVIEWER_PACKET_LOCAL_ONLY_SCHEMA_VERSION
    assert tuple(request["body_full_packet_local_only_required_field_refs"]) == r51.P7_R51_BODY_FULL_PACKET_LOCAL_ONLY_REQUIRED_FIELD_REFS
    assert request["packet_kind"] == r51.P7_R51_PACKET_KIND
    assert request["review_kind"] == r51.P7_R51_REVIEW_KIND
    assert request["review_prompt_version"] == r51.P7_R51_REVIEW_PROMPT_VERSION
    assert request["local_root_ref"] != "not_authorized"
    assert request["root_path_exposed"] is False
    assert request["local_absolute_path_included"] is False
    assert request["disposal_plan_ready"] is True
    assert request["local_only_required"] is True
    assert request["must_not_export"] is True
    assert request["disposal_required"] is True
    assert request["local_only_body_full_generation_allowed"] is True
    assert request["local_only_body_full_packet_generation_request_created_here"] is True
    assert request["body_full_packet_generation_request_created_here"] is True
    assert request["optional_writer_boundary_materialized_here"] is True
    assert request["optional_writer_execution_supported_later"] is True
    assert request["optional_writer_executed_here"] is False
    assert request["optional_writer_public_runtime_callable"] is False
    assert request["optional_writer_local_root_path_included"] is False
    assert request["optional_writer_body_content_included_here"] is False
    assert request["optional_writer_body_content_hash_stored_here"] is False
    assert request["body_full_packet_generated_here"] is False
    assert request["body_full_packets_created_local_only"] is False
    assert request["question_text_created_here"] is False
    assert request["execution_blocker_ids"] == []
    assert request["r53_7_local_only_body_full_packet_generation_request_built"] is True
    assert request["next_required_step"] == r53.P7_R53_R7_NEXT_REQUIRED_STEP_REF

    for row in request["packet_generation_request_rows"]:
        assert row["local_only_required"] is True
        assert row["must_not_export"] is True
        assert row["disposal_required"] is True
        assert row["body_full_packet_materialized_here"] is False
        assert row["local_file_written_here"] is False
        assert row["local_absolute_path_included"] is False
        assert row["body_content_hash_stored_here"] is False
        assert row["body_free"] is True

    _assert_body_free_no_release_or_runtime_promotion(request)
    _assert_no_body_payload_key_like_values(request)


@pytest.mark.parametrize(
    "key,value",
    [
        ("root_path_exposed", True),
        ("local_absolute_path_included", True),
        ("optional_writer_executed_here", True),
        ("optional_writer_public_runtime_callable", True),
        ("optional_writer_local_root_path_included", True),
        ("optional_writer_body_content_included_here", True),
        ("optional_writer_body_content_hash_stored_here", True),
        ("body_full_packet_generated_here", True),
        ("body_full_packets_created_local_only", True),
        ("local_packet_exported_allowed", True),
        ("content_hash_of_body_stored_allowed", True),
        ("export_candidate_refs_stored_here", True),
        ("export_candidate_body_stored_here", True),
        ("question_text_created_here", True),
        ("actual_human_review_run_here", True),
        ("actual_manual_review_run_here", True),
        ("p8_start_allowed", True),
        ("release_allowed", True),
        ("runtime_changed_here", True),
    ],
)
def test_r53_r7_rejects_writer_execution_path_body_hash_export_question_review_or_release_promotion(
    tmp_path: Path,
    key: str,
    value: object,
) -> None:
    request = r53.build_p7_r53_local_only_body_full_packet_generation_request_bodyfree(
        case_manifest_freeze=_r53_r6_ready(tmp_path),
    )
    request[key] = value
    with pytest.raises(ValueError):
        r53.assert_p7_r53_local_only_body_full_packet_generation_request_bodyfree_contract(request)


def test_r53_r7_rejects_packet_request_row_claiming_local_file_write_or_body_hash(tmp_path: Path) -> None:
    request = r53.build_p7_r53_local_only_body_full_packet_generation_request_bodyfree(
        case_manifest_freeze=_r53_r6_ready(tmp_path),
    )
    request["packet_generation_request_rows"][0]["local_file_written_here"] = True
    with pytest.raises(ValueError):
        r53.assert_p7_r53_local_only_body_full_packet_generation_request_bodyfree_contract(request)
