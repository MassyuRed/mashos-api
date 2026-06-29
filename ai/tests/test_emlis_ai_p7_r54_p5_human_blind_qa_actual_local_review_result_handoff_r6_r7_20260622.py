# -*- coding: utf-8 -*-
from __future__ import annotations

import json
from copy import deepcopy

import pytest

import emlis_ai_p7_r54_p5_human_blind_qa_actual_local_review_result_handoff as r54


FORBIDDEN_DUMP_TOKENS = (
    '"raw_input":',
    '"comment_text":',
    '"returned_emlis_surface":',
    '"current_input_review_surface":',
    '"bounded_owned_history_review_surface":',
    '"reviewer_free_text":',
    '"reviewer_notes":',
    '"question_text":',
    '"draft_question_text":',
    '"local_absolute_path":',
    '"body_content_hash":',
    '"packet_content_hash":',
    '"terminal_output": "',
    '"stdout":',
    '"stderr":',
)
FORBIDDEN_TRUE_TOKENS = (
    '"release_allowed": true',
    '"p7_complete": true',
    '"p8_start_allowed": true',
    '"p6_limited_human_readfeel_start_allowed": true',
    '"question_trigger_logic_implemented": true',
    '"api_db_rn_response_key_changed_here": true',
    '"runtime_changed_here": true',
    '"actual_human_review_run_here": true',
    '"actual_manual_review_run_here": true',
    '"body_full_packet_generated_here": true',
    '"actual_body_full_packet_generated_here": true',
    '"actual_rating_rows_materialized_here": true',
    '"actual_question_need_observation_rows_materialized_here": true',
    '"actual_disposal_receipt_materialized_here": true',
    '"p5_human_blind_qa_confirmed_candidate": true',
)


def _assert_body_free_no_promotion(material: dict[str, object]) -> None:
    dumped = json.dumps(material, ensure_ascii=False, sort_keys=True).lower()
    for forbidden in FORBIDDEN_DUMP_TOKENS:
        assert forbidden not in dumped
    for forbidden in FORBIDDEN_TRUE_TOKENS:
        assert forbidden not in dumped


def _ready_root(tmp_path) -> str:
    root = tmp_path / "r54_external_local_review_root"
    root.mkdir()
    return str(root)


def _r3_ready(tmp_path) -> dict[str, object]:
    preflight = r54.build_p7_r54_local_only_actual_review_preflight_bodyfree(
        validation_evidence_intake=r54.build_p7_r54_validation_evidence_intake_bodyfree(),
        local_review_root=_ready_root(tmp_path),
        explicit_allow_token=r54.P7_R54_EXPLICIT_LOCAL_REVIEW_ALLOW_TOKEN_REF,
        purge_plan=r54.build_p7_r54_default_local_only_purge_plan_bodyfree(),
        export_candidate_refs=("bodyfree/result_handoff.json",),
    )
    assert preflight["preflight_status"] == "R54_LOCAL_REVIEW_PREFLIGHT_READY"
    return preflight


def _r4_ready(tmp_path) -> dict[str, object]:
    envelope = r54.build_p7_r54_actual_review_session_envelope_bodyfree(
        local_only_actual_review_preflight=_r3_ready(tmp_path),
    )
    assert envelope["envelope_status"] == "READY_FOR_24_CASE_MANIFEST_FREEZE"
    return envelope


def _r5_ready(tmp_path) -> dict[str, object]:
    manifest = r54.build_p7_r54_24_case_manifest_freeze_bodyfree(
        actual_review_session_envelope=_r4_ready(tmp_path),
    )
    assert manifest["manifest_status"] == "READY_FOR_LOCAL_ONLY_PACKET_GENERATION_REQUEST"
    return manifest


def _r6_ready(tmp_path) -> dict[str, object]:
    request = r54.build_p7_r54_local_only_body_full_packet_generation_request_bodyfree(
        case_manifest_freeze=_r5_ready(tmp_path),
    )
    assert request["generation_request_status"] == "READY_FOR_PACKET_COMPLETENESS_EXPORT_DENYLIST_SCAN"
    assert r54.assert_p7_r54_local_only_body_full_packet_generation_request_bodyfree_contract(request) is True
    return request


def _completion_rows(request: dict[str, object]) -> list[dict[str, object]]:
    return [
        r54.build_p7_r54_packet_completion_scan_row_bodyfree(
            blind_case_id=row["blind_case_id"],
            packet_ref_id=row["packet_ref_id"],
            index=index,
        )
        for index, row in enumerate(request["packet_generation_request_rows"], start=1)
    ]


def _r7_ready(tmp_path) -> dict[str, object]:
    request = _r6_ready(tmp_path)
    scan = r54.build_p7_r54_packet_completeness_export_denylist_scan_bodyfree(
        packet_generation_request=request,
        packet_completion_rows=_completion_rows(request),
        export_candidate_refs=("bodyfree/result_handoff.json", "bodyfree/disposal_receipt.json"),
    )
    assert scan["packet_completeness_scan_status"] == "R54_PACKET_COMPLETENESS_EXPORT_DENYLIST_SCAN_READY"
    assert r54.assert_p7_r54_packet_completeness_export_denylist_scan_bodyfree_contract(scan) is True
    return scan


def test_r54_r6_blocks_by_default_before_r5_manifest_ready() -> None:
    request = r54.build_p7_r54_local_only_body_full_packet_generation_request_bodyfree()

    assert set(request) == set(r54.P7_R54_LOCAL_ONLY_BODY_FULL_PACKET_GENERATION_REQUEST_REQUIRED_FIELD_REFS)
    assert request["schema_version"] == r54.P7_R54_LOCAL_ONLY_BODY_FULL_PACKET_GENERATION_REQUEST_SCHEMA_VERSION
    assert request["policy_section"] == "R54-6_local_only_body_full_packet_generation_request"
    assert request["generation_request_status"] == "BLOCKED_BY_R54_5_MANIFEST"
    assert request["r5_manifest_ready_for_packet_request"] is False
    assert request["packet_generation_request_rows"] == []
    assert request["packet_generation_request_row_count"] == 0
    assert request["local_only_body_full_generation_allowed"] is False
    assert request["body_full_packet_generation_request_created_here"] is False
    assert request["body_full_packet_generated_here"] is False
    assert "r54_packet_generation_request_manifest_not_ready" in request["execution_blocker_ids"]
    assert request["r54_6_local_only_body_full_packet_generation_request_built"] is False
    assert request["next_required_step"] == r54.P7_R54_R6_BLOCKED_NEXT_REQUIRED_STEP_REF

    assert r54.assert_p7_r54_local_only_body_full_packet_generation_request_bodyfree_contract(request) is True
    _assert_body_free_no_promotion(request)


def test_r54_r6_ready_creates_body_free_request_without_generation(tmp_path) -> None:
    request = _r6_ready(tmp_path)

    assert request["review_session_status"] == "R54_READY_FOR_PACKET_COMPLETENESS_EXPORT_DENYLIST_SCAN"
    assert request["r5_manifest_ready_for_packet_request"] is True
    assert request["request_is_body_free"] is True
    assert request["required_case_count"] == 24
    assert request["manifest_case_count"] == 24
    assert request["packet_generation_request_row_count"] == 24
    assert len(request["packet_generation_request_rows"]) == 24
    assert len(request["packet_request_packet_ref_ids"]) == 24
    assert len(request["packet_request_blind_case_ids"]) == 24
    assert request["packet_request_packet_ref_ids_unique"] is True
    assert request["packet_request_case_ref_ids_unique"] is True
    assert request["packet_request_blind_case_ids_unique"] is True
    assert request["blind_case_id_case_ref_separated"] is True
    assert request["blind_case_id_packet_ref_separated"] is True
    assert request["case_ref_id_packet_ref_separated"] is True
    assert request["explicit_allow_verified_by_r54_3"] is True
    assert request["purge_plan_verified_by_r54_3"] is True
    assert request["export_denylist_present_by_r54_3"] is True
    assert request["retention_policy_present_by_r54_3"] is True
    assert request["local_only_body_full_generation_allowed"] is True
    assert request["body_full_packet_generation_request_created_here"] is True
    assert request["body_full_writer_invocation_allowed_only_with_explicit_allow"] is True
    assert request["body_full_writer_invoked_here"] is False
    assert request["body_full_packet_generated_here"] is False
    assert request["actual_body_full_packet_generated_here"] is False
    assert request["actual_human_review_run_here"] is False
    assert request["execution_blocker_ids"] == []
    assert tuple(request["implemented_steps"]) == r54.P7_R54_R6_IMPLEMENTED_STEPS
    assert tuple(request["not_yet_implemented_steps"]) == r54.P7_R54_R6_NOT_YET_IMPLEMENTED_STEPS
    assert request["next_required_step"] == r54.P7_R54_R6_NEXT_REQUIRED_STEP_REF

    first_row = request["packet_generation_request_rows"][0]
    assert set(first_row) == set(r54.P7_R54_PACKET_GENERATION_REQUEST_ROW_REQUIRED_FIELD_REFS)
    assert first_row["request_status_ref"] == "REQUEST_READY_NOT_GENERATED"
    assert first_row["local_only_required"] is True
    assert first_row["must_not_export"] is True
    assert first_row["disposal_required"] is True
    assert first_row["body_full_packet_materialized_here"] is False
    assert first_row["body_full_writer_invoked_here"] is False
    assert first_row["raw_input_included"] is False
    assert first_row["returned_surface_included"] is False
    assert first_row["history_body_included"] is False
    assert first_row["question_text_included"] is False

    _assert_body_free_no_promotion(request)


@pytest.mark.parametrize(
    "key,value",
    [
        ("local_absolute_path_included", True),
        ("body_content_hash_included", True),
        ("packet_content_hash_included", True),
        ("body_full_writer_invoked_here", True),
        ("body_full_packet_generated_here", True),
        ("actual_body_full_packet_generated_here", True),
        ("raw_input_included", True),
        ("returned_surface_included", True),
        ("history_body_included", True),
        ("question_text_included", True),
        ("actual_human_review_run_here", True),
        ("p5_human_blind_qa_confirmed_candidate", True),
        ("p8_start_allowed", True),
        ("release_allowed", True),
    ],
)
def test_r54_r6_rejects_body_leak_generation_review_or_promotion_mutation(tmp_path, key: str, value: object) -> None:
    request = _r6_ready(tmp_path)
    request[key] = value
    with pytest.raises(ValueError):
        r54.assert_p7_r54_local_only_body_full_packet_generation_request_bodyfree_contract(request)


def test_r54_r6_rejects_request_row_materializing_body_full_packet(tmp_path) -> None:
    request = _r6_ready(tmp_path)
    request["packet_generation_request_rows"][0] = deepcopy(request["packet_generation_request_rows"][0])
    request["packet_generation_request_rows"][0]["body_full_packet_materialized_here"] = True
    with pytest.raises(ValueError):
        r54.assert_p7_r54_local_only_body_full_packet_generation_request_bodyfree_contract(request)


def test_r54_r7_blocks_when_generation_request_is_not_ready() -> None:
    scan = r54.build_p7_r54_packet_completeness_export_denylist_scan_bodyfree()

    assert scan["schema_version"] == r54.P7_R54_PACKET_COMPLETENESS_EXPORT_DENYLIST_SCAN_SCHEMA_VERSION
    assert set(scan) == set(r54.P7_R54_PACKET_COMPLETENESS_EXPORT_DENYLIST_SCAN_REQUIRED_FIELD_REFS)
    assert scan["policy_section"] == "R54-7_packet_completeness_export_denylist_scan"
    assert scan["review_session_status"] == "R54_PACKET_SCAN_BLOCKED"
    assert scan["packet_completeness_scan_status"] == "R54_PACKET_SCAN_BLOCKED"
    assert scan["r6_ready_for_packet_scan"] is False
    assert scan["packet_completion_rows"] == []
    assert "r54_packet_generation_request_manifest_not_ready" in scan["execution_blocker_ids"]
    assert scan["ready_for_actual_human_review"] is False
    assert scan["local_packet_exported"] is False
    assert scan["violation_routes_to_purge_before_review"] is False
    assert scan["next_required_step"] == r54.P7_R54_R7_BLOCKED_NEXT_REQUIRED_STEP_REF

    assert r54.assert_p7_r54_packet_completeness_export_denylist_scan_bodyfree_contract(scan) is True
    _assert_body_free_no_promotion(scan)


def test_r54_r7_ready_scans_24_body_free_completion_rows_and_export_denylist(tmp_path) -> None:
    request = _r6_ready(tmp_path)
    rows = _completion_rows(request)
    scan = r54.build_p7_r54_packet_completeness_export_denylist_scan_bodyfree(
        packet_generation_request=request,
        packet_completion_rows=rows,
        export_candidate_refs=("bodyfree/result_handoff.json", "bodyfree/disposal_receipt.json"),
    )

    assert scan["review_session_status"] == "R54_READY_FOR_ACTUAL_HUMAN_REVIEW"
    assert scan["packet_completeness_scan_status"] == "R54_PACKET_COMPLETENESS_EXPORT_DENYLIST_SCAN_READY"
    assert scan["r6_ready_for_packet_scan"] is True
    assert scan["packet_request_row_count"] == 24
    assert scan["packet_completion_row_count"] == 24
    assert len(scan["packet_completion_rows"]) == 24
    assert scan["packet_completion_row_count_matches_request"] is True
    assert scan["all_required_packet_fields_present"] is True
    assert scan["packet_completion_blind_case_ids_unique"] is True
    assert scan["packet_completion_packet_ref_ids_unique"] is True
    assert scan["export_candidate_count"] == 2
    assert scan["export_denied_candidate_count"] == 0
    assert scan["export_denylist_violation_refs"] == []
    assert scan["body_full_export_candidate_ref_count"] == 0
    assert scan["export_candidate_refs_body_free_only"] is True
    assert scan["local_packet_exported"] is False
    assert scan["body_full_packet_generated_here"] is False
    assert scan["actual_body_full_packet_generated_here"] is False
    assert scan["actual_human_review_run_here"] is False
    assert scan["ready_for_actual_human_review"] is True
    assert scan["violation_routes_to_purge_before_review"] is False
    assert tuple(scan["implemented_steps"]) == r54.P7_R54_R7_IMPLEMENTED_STEPS
    assert tuple(scan["not_yet_implemented_steps"]) == r54.P7_R54_R7_NOT_YET_IMPLEMENTED_STEPS
    assert scan["next_required_step"] == r54.P7_R54_R7_NEXT_REQUIRED_STEP_REF

    row = scan["packet_completion_rows"][0]
    assert set(row) == set(r54.P7_R54_PACKET_COMPLETION_SCAN_ROW_REQUIRED_FIELD_REFS)
    assert row["completion_status_ref"] == "LOCAL_ONLY_PACKET_PRESENT_BODY_FREE_SCAN"
    assert row["packet_present_local_only"] is True
    assert row["required_body_full_review_packet_fields_present"] is True
    assert row["completion_scan_body_free"] is True
    assert row["body_full_packet_materialized_here"] is False
    assert row["local_packet_exported"] is False
    assert row["local_absolute_path_included"] is False
    assert row["body_content_hash_included"] is False

    _assert_body_free_no_promotion(scan)


def test_r54_r7_export_denylist_violation_blocks_review_and_requires_purge(tmp_path) -> None:
    request = _r6_ready(tmp_path)
    rows = _completion_rows(request)
    scan = r54.build_p7_r54_packet_completeness_export_denylist_scan_bodyfree(
        packet_generation_request=request,
        packet_completion_rows=rows,
        export_candidate_refs=("body_full_packets.local_only/p7_r54_case_001.local_only.json",),
    )

    assert scan["packet_completeness_scan_status"] == "BLOCKED_BY_PACKET_COMPLETENESS_OR_EXPORT_DENYLIST"
    assert scan["ready_for_actual_human_review"] is False
    assert scan["export_denied_candidate_count"] == 1
    assert scan["export_denylist_violation_refs"] == ["r47_export_denylist_pattern_match"]
    assert "r54_packet_export_candidate_body_full_ref_detected" in scan["execution_blocker_ids"]
    assert scan["local_packet_exported"] is False
    assert scan["violation_routes_to_purge_before_review"] is True
    assert scan["next_required_step"] == r54.P7_R54_R7_PURGE_REQUIRED_NEXT_STEP_REF

    assert r54.assert_p7_r54_packet_completeness_export_denylist_scan_bodyfree_contract(scan) is True
    _assert_body_free_no_promotion(scan)


def test_r54_r7_missing_completion_row_blocks_review(tmp_path) -> None:
    request = _r6_ready(tmp_path)
    rows = _completion_rows(request)[:-1]
    scan = r54.build_p7_r54_packet_completeness_export_denylist_scan_bodyfree(
        packet_generation_request=request,
        packet_completion_rows=rows,
    )

    assert scan["packet_completion_row_count"] == 23
    assert scan["packet_completion_row_count_matches_request"] is False
    assert "r54_packet_completeness_row_count_mismatch" in scan["execution_blocker_ids"]
    assert scan["ready_for_actual_human_review"] is False


@pytest.mark.parametrize(
    "key,value",
    [
        ("local_packet_exported", True),
        ("local_absolute_path_included", True),
        ("body_content_hash_included", True),
        ("packet_content_hash_included", True),
        ("body_full_packet_generated_here", True),
        ("actual_body_full_packet_generated_here", True),
        ("raw_input_included", True),
        ("returned_surface_included", True),
        ("history_body_included", True),
        ("question_text_included", True),
        ("actual_human_review_run_here", True),
        ("p6_limited_human_readfeel_start_allowed", True),
        ("p8_start_allowed", True),
        ("release_allowed", True),
    ],
)
def test_r54_r7_rejects_export_body_leak_review_or_promotion_mutation(tmp_path, key: str, value: object) -> None:
    scan = _r7_ready(tmp_path)
    scan[key] = value
    with pytest.raises(ValueError):
        r54.assert_p7_r54_packet_completeness_export_denylist_scan_bodyfree_contract(scan)


def test_r54_r7_rejects_packet_completion_row_with_body_hash_or_local_path(tmp_path) -> None:
    scan = _r7_ready(tmp_path)
    scan["packet_completion_rows"][0] = deepcopy(scan["packet_completion_rows"][0])
    scan["packet_completion_rows"][0]["local_absolute_path_included"] = True
    with pytest.raises(ValueError):
        r54.assert_p7_r54_packet_completeness_export_denylist_scan_bodyfree_contract(scan)
