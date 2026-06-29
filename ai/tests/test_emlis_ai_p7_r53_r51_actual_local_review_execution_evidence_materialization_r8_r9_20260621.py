# -*- coding: utf-8 -*-
"""P7-R53 R8/R9 tests for packet scan and reviewer instruction freeze."""

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
    local_root.mkdir(exist_ok=True)
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


@lru_cache(maxsize=1)
def _cached_r53_r7_ready() -> tuple[dict[str, object]]:
    root = Path("/tmp/cocolon_r53_8_9_cached_local_review_root")
    root.mkdir(parents=True, exist_ok=True)
    request = r53.build_p7_r53_local_only_body_full_packet_generation_request_bodyfree(
        case_manifest_freeze=_r53_r6_ready(root),
    )
    assert r53.assert_p7_r53_local_only_body_full_packet_generation_request_bodyfree_contract(request) is True
    return (request,)


def _r53_r7_ready(tmp_path: Path) -> dict[str, object]:
    _ = tmp_path
    return deepcopy(_cached_r53_r7_ready()[0])


def _packet_completion_rows_from_r53_r7_request(request: dict[str, object]) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for row in request["packet_generation_request_rows"]:  # type: ignore[index]
        assert isinstance(row, dict)
        rows.append(
            {
                "blind_case_id": row["blind_case_id"],
                "case_ref_id": row["case_ref_id"],
                "packet_ref_id": row["packet_ref_id"],
                "packet_present_local_only": True,
                "required_field_refs_present": True,
                "local_only_marker_present": True,
                "must_not_export_marker_present": True,
                "disposal_required_marker_present": True,
                "export_candidate_detected": False,
                "export_denylist_violation_detected": False,
            }
        )
    return rows


@lru_cache(maxsize=1)
def _cached_r53_r8_ready() -> tuple[dict[str, object]]:
    request = deepcopy(_cached_r53_r7_ready()[0])
    scan = r53.build_p7_r53_packet_completeness_export_denylist_scan_bodyfree(
        local_only_body_full_packet_generation_request=request,
        packet_completion_rows=_packet_completion_rows_from_r53_r7_request(request),
    )
    assert r53.assert_p7_r53_packet_completeness_export_denylist_scan_bodyfree_contract(scan) is True
    return (scan,)


def _r53_r8_ready(tmp_path: Path) -> dict[str, object]:
    _ = tmp_path
    return deepcopy(_cached_r53_r8_ready()[0])


def test_r53_r8_default_packet_scan_is_blocked_without_ready_request_and_exposes_no_packet_body() -> None:
    scan = r53.build_p7_r53_packet_completeness_export_denylist_scan_bodyfree()

    assert scan["schema_version"] == r53.P7_R53_PACKET_COMPLETENESS_EXPORT_DENYLIST_SCAN_SCHEMA_VERSION
    assert set(scan) == set(r53.P7_R53_PACKET_COMPLETENESS_EXPORT_DENYLIST_SCAN_REQUIRED_FIELD_REFS)
    assert scan["policy_section"] == "R53-8_packet_completeness_export_denylist_scan"
    assert scan["current_received_snapshot_refs"] == r53.P7_R53_CURRENT_RECEIVED_SNAPSHOT_REFS
    assert scan["r7_generation_request_ready_for_packet_scan"] is False
    assert scan["packet_completeness_scan_status"] == "BLOCKED_BY_R53_7_GENERATION_REQUEST"
    assert scan["review_session_status"] == "PRECHECK_BLOCKED"
    assert scan["packet_scan_row_count"] == 0
    assert scan["packet_scan_rows"] == []
    assert scan["all_required_packets_present"] is False
    assert scan["body_full_packet_completeness_verified"] is False
    assert scan["r53_8_packet_completeness_export_denylist_scan_built"] is False
    assert scan["local_absolute_path_included"] is False
    assert scan["packet_body_included_here"] is False
    assert scan["body_content_hash_stored_here"] is False
    assert scan["body_full_packet_generated_here"] is False
    assert scan["body_full_packets_created_local_only"] is False
    assert scan["actual_human_review_run_here"] is False
    assert scan["execution_blocker_ids"]
    assert scan["open_execution_blocker_ids"] == scan["execution_blocker_ids"]
    assert scan["next_required_step"] == r53.P7_R53_R8_BLOCKED_NEXT_REQUIRED_STEP_REF
    assert tuple(scan["implemented_steps"]) == r53.P7_R53_R8_IMPLEMENTED_STEPS
    assert tuple(scan["not_yet_implemented_steps"]) == r53.P7_R53_R8_NOT_YET_IMPLEMENTED_STEPS
    assert r51.assert_p7_r51_body_full_packet_completeness_export_denylist_scan_bodyfree_contract(
        scan["r51_r6_packet_completeness_scan_bodyfree"]
    ) is True

    _assert_body_free_no_release_or_runtime_promotion(scan)
    _assert_no_body_payload_key_like_values(scan)


def test_r53_r8_ready_request_without_completion_rows_stays_blocked_instead_of_inventing_packet_presence(
    tmp_path: Path,
) -> None:
    request = _r53_r7_ready(tmp_path)
    scan = r53.build_p7_r53_packet_completeness_export_denylist_scan_bodyfree(
        local_only_body_full_packet_generation_request=request,
    )

    assert scan["r7_generation_request_ready_for_packet_scan"] is True
    assert scan["packet_completeness_scan_status"] == "BLOCKED_BY_PACKET_COMPLETENESS_OR_EXPORT_DENYLIST"
    assert scan["body_full_packet_completeness_verified"] is False
    assert "r53_packet_completion_evidence_missing" in scan["execution_blocker_ids"]
    assert scan["packet_scan_row_count"] == 0
    assert scan["next_required_step"] == r53.P7_R53_R8_BLOCKED_NEXT_REQUIRED_STEP_REF

    _assert_body_free_no_release_or_runtime_promotion(scan)
    _assert_no_body_payload_key_like_values(scan)


def test_r53_r8_ready_packet_scan_accepts_24_bodyfree_completion_rows_without_path_hash_or_body(
    tmp_path: Path,
) -> None:
    request = _r53_r7_ready(tmp_path)
    scan = r53.build_p7_r53_packet_completeness_export_denylist_scan_bodyfree(
        local_only_body_full_packet_generation_request=request,
        packet_completion_rows=_packet_completion_rows_from_r53_r7_request(request),
    )

    assert scan["packet_completeness_scan_status"] == "READY_FOR_REVIEWER_INSTRUCTION_RATING_FORM_FREEZE"
    assert scan["review_session_status"] == "R53_PACKET_COMPLETENESS_EXPORT_DENYLIST_SCAN_READY"
    assert scan["r7_generation_request_ready_for_packet_scan"] is True
    assert scan["r51_r6_packet_completeness_scan_status"] == "READY_FOR_REVIEWER_INSTRUCTION_RATING_FORM_FREEZE"
    assert scan["r51_r6_next_required_step"] == r51.P7_R51_R6_NEXT_REQUIRED_STEP_REF
    assert scan["required_case_count"] == r51.P7_R51_REQUIRED_CASE_COUNT
    assert scan["request_row_count"] == 24
    assert scan["packet_scan_row_count"] == 24
    assert len(scan["packet_scan_rows"]) == 24
    assert scan["expected_packet_ref_count"] == 24
    assert scan["present_packet_ref_count"] == 24
    assert scan["missing_packet_ref_count"] == 0
    assert scan["incomplete_packet_ref_count"] == 0
    assert scan["packet_ref_ids_unique"] is True
    assert scan["case_ref_ids_unique"] is True
    assert scan["blind_case_ids_unique"] is True
    assert scan["all_required_packets_present"] is True
    assert scan["all_required_fields_present"] is True
    assert scan["all_local_only_markers_present"] is True
    assert scan["all_must_not_export_markers_present"] is True
    assert scan["all_disposal_required_markers_present"] is True
    assert scan["body_full_packet_completeness_verified"] is True
    assert scan["body_full_packet_export_violation_detected"] is False
    assert scan["denied_export_candidate_count"] == 0
    assert scan["row_export_denylist_violation_count"] == 0
    assert scan["local_absolute_path_included"] is False
    assert scan["packet_body_included_here"] is False
    assert scan["body_content_hash_stored_here"] is False
    assert scan["execution_blocker_ids"] == []
    assert scan["r53_8_packet_completeness_export_denylist_scan_built"] is True
    assert scan["next_required_step"] == r53.P7_R53_R8_NEXT_REQUIRED_STEP_REF

    for row in scan["packet_scan_rows"]:
        assert row["completion_status_ref"] == "PACKET_PRESENT_LOCAL_ONLY"
        assert row["packet_present_local_only"] is True
        assert row["required_field_refs_present"] is True
        assert row["local_only_marker_present"] is True
        assert row["must_not_export_marker_present"] is True
        assert row["disposal_required_marker_present"] is True
        assert row["body_full_packet_materialized_here"] is False
        assert row["body_full_packet_body_copied_here"] is False
        assert row["local_absolute_path_included"] is False
        assert row["body_content_hash_stored_here"] is False
        assert row["body_free"] is True

    _assert_body_free_no_release_or_runtime_promotion(scan)
    _assert_no_body_payload_key_like_values(scan)


@pytest.mark.parametrize(
    "key,value",
    [
        ("root_path_exposed", True),
        ("local_absolute_path_included", True),
        ("packet_body_included_here", True),
        ("packet_body_copied_here", True),
        ("body_content_hash_stored_here", True),
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
def test_r53_r8_rejects_path_body_hash_export_question_review_or_release_promotion(
    tmp_path: Path,
    key: str,
    value: object,
) -> None:
    scan = _r53_r8_ready(tmp_path)
    scan[key] = value
    with pytest.raises(ValueError):
        r53.assert_p7_r53_packet_completeness_export_denylist_scan_bodyfree_contract(scan)


def test_r53_r8_rejects_packet_scan_row_claiming_body_copy_or_local_path(tmp_path: Path) -> None:
    scan = _r53_r8_ready(tmp_path)
    scan["packet_scan_rows"][0]["body_full_packet_body_copied_here"] = True
    with pytest.raises(ValueError):
        r53.assert_p7_r53_packet_completeness_export_denylist_scan_bodyfree_contract(scan)


def test_r53_r9_default_reviewer_instruction_form_is_blocked_without_ready_packet_scan_and_runs_no_review() -> None:
    form = r53.build_p7_r53_reviewer_instruction_rating_form_freeze_bodyfree()

    assert form["schema_version"] == r53.P7_R53_REVIEWER_INSTRUCTION_RATING_FORM_FREEZE_SCHEMA_VERSION
    assert set(form) == set(r53.P7_R53_REVIEWER_INSTRUCTION_RATING_FORM_FREEZE_REQUIRED_FIELD_REFS)
    assert form["policy_section"] == "R53-9_reviewer_instruction_rating_form_freeze"
    assert form["current_received_snapshot_refs"] == r53.P7_R53_CURRENT_RECEIVED_SNAPSHOT_REFS
    assert form["r8_packet_completeness_ready_for_reviewer_instruction_rating_form"] is False
    assert form["instruction_form_status"] == "BLOCKED_BY_R53_8_PACKET_COMPLETENESS_SCAN"
    assert form["review_session_status"] == "PRECHECK_BLOCKED"
    assert form["r53_9_reviewer_instruction_rating_form_freeze_built"] is False
    assert form["machine_auto_score_allowed"] is False
    assert form["question_need_observation_selection_required"] is True
    assert form["question_text_required"] is False
    assert form["draft_question_text_allowed"] is False
    assert form["reviewer_free_text_local_only"] is True
    assert form["reviewer_free_text_bodyfree_export_allowed"] is False
    assert form["p5_weakness_must_not_be_hidden_by_question_candidate"] is True
    assert form["actual_rating_rows_materialized_here"] is False
    assert form["actual_question_need_observation_rows_materialized_here"] is False
    assert form["actual_human_review_run_here"] is False
    assert form["body_full_packet_generated_here"] is False
    assert form["execution_blocker_ids"]
    assert form["next_required_step"] == r53.P7_R53_R9_BLOCKED_NEXT_REQUIRED_STEP_REF
    assert tuple(form["implemented_steps"]) == r53.P7_R53_R9_IMPLEMENTED_STEPS
    assert tuple(form["not_yet_implemented_steps"]) == r53.P7_R53_R9_NOT_YET_IMPLEMENTED_STEPS
    assert r51.assert_p7_r51_reviewer_instruction_rating_form_freeze_bodyfree_contract(
        form["r51_r7_instruction_rating_form_bodyfree"]
    ) is True

    _assert_body_free_no_release_or_runtime_promotion(form)
    _assert_no_body_payload_key_like_values(form)


def test_r53_r9_ready_reviewer_instruction_form_freezes_p5_rating_axes_and_question_observation_selection(
    tmp_path: Path,
) -> None:
    form = r53.build_p7_r53_reviewer_instruction_rating_form_freeze_bodyfree(
        packet_completeness_export_denylist_scan=_r53_r8_ready(tmp_path),
    )

    assert form["instruction_form_status"] == "READY_FOR_ACTUAL_REVIEW_RESULT_CAPTURE"
    assert form["review_session_status"] == "R53_REVIEWER_INSTRUCTION_RATING_FORM_READY"
    assert form["r8_packet_completeness_ready_for_reviewer_instruction_rating_form"] is True
    assert form["r51_r7_instruction_form_status"] == "READY_FOR_ACTUAL_HUMAN_REVIEW_RUN"
    assert form["r51_r7_next_required_step"] == r51.P7_R51_R7_NEXT_REQUIRED_STEP_REF
    assert form["required_case_count"] == r51.P7_R51_REQUIRED_CASE_COUNT
    assert form["packet_scan_row_count"] == 24
    assert form["review_prompt_version"] == r51.P7_R51_REVIEW_PROMPT_VERSION
    assert form["rating_axis_count"] == 6
    assert tuple(form["rating_axis_refs"]) == tuple(form["r51_r7_instruction_rating_form_bodyfree"]["rating_axis_refs"])
    assert form["rating_score_min"] == 0.0
    assert form["rating_score_max"] == 1.0
    assert form["extra_rating_axis_allowed"] is False
    assert form["machine_auto_score_allowed"] is False
    assert form["rating_row_required_for_each_case"] is True
    assert form["red_or_repair_requires_blocker"] is True
    assert form["execution_blocker_is_not_readfeel_verdict"] is True
    assert form["question_need_observation_selection_required"] is True
    assert form["question_text_required"] is False
    assert form["draft_question_text_allowed"] is False
    assert form["reviewer_free_text_local_only"] is True
    assert form["reviewer_free_text_bodyfree_export_allowed"] is False
    assert form["reviewer_free_text_to_sanitized_reason_ids_required"] is True
    assert form["p5_weakness_must_not_be_hidden_by_question_candidate"] is True
    assert form["body_full_reader_protocol_local_only"] is True
    assert form["blind_case_id_required"] is True
    assert form["case_ref_hidden_from_reviewer"] is True
    assert form["family_hidden_from_reviewer"] is True
    assert form["subscription_tier_hidden_from_reviewer"] is True
    assert form["p8_material_candidate_conditions_hidden_from_reviewer"] is True
    assert form["reviewer_instruction_materialized_for_actual_review_here"] is False
    assert form["actual_rating_rows_materialized_here"] is False
    assert form["actual_blocker_rows_materialized_here"] is False
    assert form["actual_execution_blocker_rows_materialized_here"] is False
    assert form["actual_question_need_observation_rows_materialized_here"] is False
    assert form["actual_human_review_run_here"] is False
    assert form["actual_manual_review_run_here"] is False
    assert form["body_full_packet_generated_here"] is False
    assert form["body_full_packets_created_local_only"] is False
    assert form["body_full_packet_completeness_verified"] is True
    assert form["local_only_body_full_generation_allowed"] is True
    assert form["p5_actual_review_still_not_run"] is True
    assert form["execution_blocker_ids"] == []
    assert form["r53_9_reviewer_instruction_rating_form_freeze_built"] is True
    assert form["next_required_step"] == r53.P7_R53_R9_NEXT_REQUIRED_STEP_REF

    _assert_body_free_no_release_or_runtime_promotion(form)
    _assert_no_body_payload_key_like_values(form)


@pytest.mark.parametrize(
    "key,value",
    [
        ("extra_rating_axis_allowed", True),
        ("machine_auto_score_allowed", True),
        ("question_text_required", True),
        ("draft_question_text_allowed", True),
        ("reviewer_free_text_bodyfree_export_allowed", True),
        ("reviewer_instruction_materialized_for_actual_review_here", True),
        ("actual_rating_rows_materialized_here", True),
        ("actual_blocker_rows_materialized_here", True),
        ("actual_execution_blocker_rows_materialized_here", True),
        ("actual_question_need_observation_rows_materialized_here", True),
        ("actual_human_review_run_here", True),
        ("actual_manual_review_run_here", True),
        ("body_full_packet_generated_here", True),
        ("body_full_packets_created_local_only", True),
        ("p8_start_allowed", True),
        ("release_allowed", True),
        ("api_db_rn_response_key_changed_here", True),
        ("runtime_changed_here", True),
    ],
)
def test_r53_r9_rejects_machine_scoring_question_text_review_rows_review_run_or_release_promotion(
    tmp_path: Path,
    key: str,
    value: object,
) -> None:
    form = r53.build_p7_r53_reviewer_instruction_rating_form_freeze_bodyfree(
        packet_completeness_export_denylist_scan=_r53_r8_ready(tmp_path),
    )
    form[key] = value
    with pytest.raises(ValueError):
        r53.assert_p7_r53_reviewer_instruction_rating_form_freeze_bodyfree_contract(form)
