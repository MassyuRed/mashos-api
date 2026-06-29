# -*- coding: utf-8 -*-
"""P7-R53 R10/R11 tests for sanitized actual review capture and rating rows."""

from __future__ import annotations

from copy import deepcopy
from functools import lru_cache
from pathlib import Path

import pytest

import emlis_ai_p7_r51_p5_human_blind_qa_actual_local_manual_run as r51
import emlis_ai_p7_r53_r51_actual_local_review_execution_evidence_materialization as r53


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


def _assert_common_no_p8_release_or_runtime_change(material: dict[str, object]) -> None:
    assert material["body_free"] is True
    assert material["git_connection_required"] is False
    assert material["git_checked"] is False
    assert material["p8_start_allowed"] is False
    assert material["p7_complete"] is False
    assert material["release_allowed"] is False
    assert material["api_db_rn_response_key_changed_here"] is False
    assert material["runtime_changed_here"] is False
    assert material["body_full_packet_generated_here"] is False
    assert material["body_full_packets_created_local_only"] is False
    assert material["actual_reviewer_notes_materialized_here"] is False


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


def _r53_r4_ready(root: Path) -> dict[str, object]:
    local_root = root / "r53_local_review_root"
    local_root.mkdir(parents=True, exist_ok=True)
    preflight = r53.build_p7_r53_local_root_explicit_allow_purge_plan_preflight(
        current_snapshot_override_adoption=_r53_r3_green_override(),
        local_review_root=str(local_root),
        repo_roots=[str(Path.cwd())],
        export_roots=[str(root / "export_root")],
        explicit_allow_token=r51.P7_R51_EXPLICIT_ACTUAL_LOCAL_MANUAL_RUN_ALLOW_TOKEN_REF,
        purge_plan=r53.build_p7_r53_default_local_only_purge_plan_bodyfree(),
    )
    assert r53.assert_p7_r53_local_root_explicit_allow_purge_plan_preflight_contract(preflight) is True
    return preflight


def _r53_r6_ready(root: Path) -> dict[str, object]:
    envelope = r53.build_p7_r53_actual_review_session_envelope_bodyfree(
        local_root_explicit_allow_purge_plan_preflight=_r53_r4_ready(root),
    )
    assert r53.assert_p7_r53_actual_review_session_envelope_bodyfree_contract(envelope) is True
    manifest = r53.build_p7_r53_24_case_manifest_freeze_bodyfree(actual_review_session_envelope=envelope)
    assert r53.assert_p7_r53_24_case_manifest_freeze_bodyfree_contract(manifest) is True
    return manifest


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
def _cached_r53_r9_ready() -> tuple[dict[str, object], dict[str, object]]:
    root = Path("/tmp/cocolon_r53_10_11_cached_local_review_root")
    root.mkdir(parents=True, exist_ok=True)
    manifest = _r53_r6_ready(root)
    request = r53.build_p7_r53_local_only_body_full_packet_generation_request_bodyfree(
        case_manifest_freeze=manifest,
    )
    assert r53.assert_p7_r53_local_only_body_full_packet_generation_request_bodyfree_contract(request) is True
    scan = r53.build_p7_r53_packet_completeness_export_denylist_scan_bodyfree(
        local_only_body_full_packet_generation_request=request,
        packet_completion_rows=_packet_completion_rows_from_r53_r7_request(request),
    )
    assert r53.assert_p7_r53_packet_completeness_export_denylist_scan_bodyfree_contract(scan) is True
    form = r53.build_p7_r53_reviewer_instruction_rating_form_freeze_bodyfree(
        packet_completeness_export_denylist_scan=scan,
    )
    assert r53.assert_p7_r53_reviewer_instruction_rating_form_freeze_bodyfree_contract(form) is True
    return (form, manifest)


def _r53_r9_ready_and_manifest() -> tuple[dict[str, object], dict[str, object]]:
    form, manifest = _cached_r53_r9_ready()
    return deepcopy(form), deepcopy(manifest)


def _sanitized_review_result_rows() -> list[dict[str, object]]:
    form, manifest = _r53_r9_ready_and_manifest()
    rows: list[dict[str, object]] = []
    for case in manifest["controller_manifest_rows"]:  # type: ignore[index]
        assert isinstance(case, dict)
        rows.append(
            {
                "blind_case_id": case["blind_case_id"],
                "axis_scores": {axis: 1.0 for axis in form["rating_axis_refs"]},  # type: ignore[index]
                "verdict": "PASS",
                "sanitized_reason_ids": [],
                "blocker_ids": [],
                "question_need_primary_class": "no_question_needed_emlis_can_observe",
                "ambiguity_kind_refs": ["no_material_ambiguity"],
                "one_question_fit_ref": "not_needed",
                "repair_required_refs": ["no_repair_required"],
                "reviewer_free_text_included": False,
                "question_text_included": False,
                "draft_question_text_included": False,
                "machine_auto_score_used": False,
                "machine_metrics_used_for_readfeel": False,
                "body_removed": False,
                "body_free": True,
            }
        )
    return rows


@lru_cache(maxsize=1)
def _cached_r53_r10_ready() -> tuple[dict[str, object]]:
    form, manifest = _r53_r9_ready_and_manifest()
    capture = r53.build_p7_r53_actual_human_review_result_capture_bodyfree(
        reviewer_instruction_rating_form_freeze=form,
        case_manifest_freeze=manifest,
        review_result_rows=_sanitized_review_result_rows(),
    )
    assert r53.assert_p7_r53_actual_human_review_result_capture_bodyfree_contract(capture) is True
    return (capture,)


def _r53_r10_ready() -> dict[str, object]:
    return deepcopy(_cached_r53_r10_ready()[0])


def test_r53_r10_default_capture_is_blocked_without_ready_form_manifest_or_sanitized_rows() -> None:
    capture = r53.build_p7_r53_actual_human_review_result_capture_bodyfree()

    assert capture["schema_version"] == r53.P7_R53_ACTUAL_HUMAN_REVIEW_RESULT_CAPTURE_SCHEMA_VERSION
    assert set(capture) == set(r53.P7_R53_ACTUAL_HUMAN_REVIEW_RESULT_CAPTURE_REQUIRED_FIELD_REFS)
    assert capture["policy_section"] == "R53-10_actual_human_review_result_capture"
    assert capture["current_received_snapshot_refs"] == r53.P7_R53_CURRENT_RECEIVED_SNAPSHOT_REFS
    assert capture["actual_review_run_status"] == "BLOCKED_BY_R53_9_OR_MISSING_SANITIZED_REVIEW_RESULTS"
    assert capture["review_result_capture_row_count"] == 0
    assert capture["review_result_capture_rows"] == []
    assert capture["all_24_cases_reviewed"] is False
    assert capture["rating_selections_captured_bodyfree"] is False
    assert capture["question_need_observation_selections_captured_bodyfree"] is False
    assert capture["actual_human_review_run_here"] is False
    assert capture["actual_manual_review_run_here"] is False
    assert capture["actual_review_result_rows_captured_here"] is False
    assert capture["p5_actual_review_still_not_run"] is True
    assert capture["execution_blocker_ids"]
    assert capture["open_execution_blocker_ids"] == capture["execution_blocker_ids"]
    assert capture["next_required_step"] == r53.P7_R53_R10_BLOCKED_NEXT_REQUIRED_STEP_REF
    assert tuple(capture["implemented_steps"]) == r53.P7_R53_R9_IMPLEMENTED_STEPS
    assert tuple(capture["not_yet_implemented_steps"]) == r53.P7_R53_R9_NOT_YET_IMPLEMENTED_STEPS

    _assert_common_no_p8_release_or_runtime_change(capture)
    _assert_no_body_payload_key_like_values(capture)


def test_r53_r10_ready_capture_accepts_24_sanitized_rows_without_body_text_path_hash_or_machine_score() -> None:
    capture = _r53_r10_ready()

    assert capture["actual_review_run_status"] == "READY_FOR_RATING_ROW_NORMALIZATION"
    assert capture["review_session_status"] == "R53_ACTUAL_REVIEW_RESULT_CAPTURE_READY"
    assert capture["r9_ready_for_actual_review_capture"] is True
    assert capture["r6_manifest_ready_for_actual_review_capture"] is True
    assert capture["r51_r8_next_required_step"] == r51.P7_R51_R8_NEXT_REQUIRED_STEP_REF
    assert capture["review_result_capture_row_count"] == 24
    assert capture["all_24_cases_reviewed"] is True
    assert capture["rating_selections_captured_bodyfree"] is True
    assert capture["question_need_observation_selections_captured_bodyfree"] is True
    assert capture["actual_human_review_run_here"] is True
    assert capture["actual_manual_review_run_here"] is True
    assert capture["actual_review_result_rows_captured_here"] is True
    assert capture["actual_rating_rows_materialized_here"] is False
    assert capture["actual_question_need_observation_rows_materialized_here"] is False
    assert capture["reviewer_free_text_included"] is False
    assert capture["question_text_included"] is False
    assert capture["draft_question_text_included"] is False
    assert capture["raw_input_or_returned_surface_included"] is False
    assert capture["machine_auto_score_allowed"] is False
    assert capture["machine_metrics_used_for_readfeel"] is False
    assert capture["execution_blocker_ids"] == []
    assert capture["p5_actual_review_still_not_run"] is False
    assert capture["r53_10_actual_human_review_result_capture_built"] is True
    assert capture["next_required_step"] == r53.P7_R53_R10_NEXT_REQUIRED_STEP_REF
    assert tuple(capture["implemented_steps"]) == r53.P7_R53_R10_IMPLEMENTED_STEPS
    assert tuple(capture["not_yet_implemented_steps"]) == r53.P7_R53_R10_NOT_YET_IMPLEMENTED_STEPS
    assert r51.assert_p7_r51_actual_human_review_run_bodyfree_contract(
        capture["r51_r8_actual_human_review_run_bodyfree"],
        allowed_true_false_key_refs=r53.P7_R53_R10_ALLOWED_TRUE_FALSE_KEY_REFS,
    ) is True
    for row in capture["review_result_capture_rows"]:  # type: ignore[index]
        assert isinstance(row, dict)
        assert set(row) == set(r51.P7_R51_ACTUAL_REVIEW_RESULT_CAPTURE_ROW_FIELD_REFS)
        assert row["verdict"] == "PASS"
        assert row["body_free"] is True
        assert row["reviewer_free_text_included"] is False
        assert row["question_text_included"] is False
        assert row["draft_question_text_included"] is False
        assert row["machine_auto_score_used"] is False
        assert row["machine_metrics_used_for_readfeel"] is False

    _assert_common_no_p8_release_or_runtime_change(capture)
    _assert_no_body_payload_key_like_values(capture)


@pytest.mark.parametrize(
    "key,value",
    [
        ("reviewer_free_text_included", True),
        ("question_text_included", True),
        ("draft_question_text_included", True),
        ("raw_input_or_returned_surface_included", True),
        ("machine_auto_score_allowed", True),
        ("machine_metrics_used_for_readfeel", True),
        ("actual_rating_rows_materialized_here", True),
        ("actual_question_need_observation_rows_materialized_here", True),
        ("actual_reviewer_notes_materialized_here", True),
        ("body_full_packet_generated_here", True),
        ("body_full_packets_created_local_only", True),
        ("p8_start_allowed", True),
        ("release_allowed", True),
        ("api_db_rn_response_key_changed_here", True),
        ("runtime_changed_here", True),
    ],
)
def test_r53_r10_rejects_body_text_machine_scoring_rating_rows_or_release_promotion(key: str, value: object) -> None:
    capture = _r53_r10_ready()
    capture[key] = value
    with pytest.raises(ValueError):
        r53.assert_p7_r53_actual_human_review_result_capture_bodyfree_contract(capture)


@pytest.mark.parametrize("forbidden_key", ["raw_input", "returned_emlis_surface", "reviewer_free_text", "question_text", "body", "body_hash"])
def test_r53_r10_rejects_sanitized_input_rows_that_attempt_to_carry_body_or_text(forbidden_key: str) -> None:
    form, manifest = _r53_r9_ready_and_manifest()
    rows = _sanitized_review_result_rows()
    rows[0][forbidden_key] = "must_not_be_captured"
    with pytest.raises(ValueError):
        r53.build_p7_r53_actual_human_review_result_capture_bodyfree(
            reviewer_instruction_rating_form_freeze=form,
            case_manifest_freeze=manifest,
            review_result_rows=rows,
        )


def test_r53_r11_default_rating_row_normalization_is_blocked_without_r10_capture() -> None:
    normalization = r53.build_p7_r53_rating_row_normalization_bodyfree()

    assert normalization["schema_version"] == r53.P7_R53_RATING_ROW_NORMALIZATION_SCHEMA_VERSION
    assert set(normalization) == set(r53.P7_R53_RATING_ROW_NORMALIZATION_REQUIRED_FIELD_REFS)
    assert normalization["policy_section"] == "R53-11_rating_row_normalization"
    assert normalization["rating_row_normalizer_status"] == "BLOCKED_BY_R53_10_ACTUAL_REVIEW_RESULT_CAPTURE"
    assert normalization["r10_actual_review_capture_ready_for_rating_normalization"] is False
    assert normalization["rating_row_count"] == 0
    assert normalization["rating_rows"] == []
    assert normalization["all_required_rating_rows_present"] is False
    assert normalization["rating_case_ref_sets_match_review_capture"] is False
    assert normalization["actual_human_review_run_here"] is False
    assert normalization["actual_manual_review_run_here"] is False
    assert normalization["actual_rating_rows_materialized_here"] is False
    assert normalization["p5_actual_review_still_not_run"] is True
    assert normalization["execution_blocker_ids"]
    assert normalization["open_execution_blocker_ids"] == normalization["execution_blocker_ids"]
    assert normalization["next_required_step"] == r53.P7_R53_R11_BLOCKED_NEXT_REQUIRED_STEP_REF
    assert tuple(normalization["implemented_steps"]) == r53.P7_R53_R9_IMPLEMENTED_STEPS
    assert tuple(normalization["not_yet_implemented_steps"]) == r53.P7_R53_R9_NOT_YET_IMPLEMENTED_STEPS

    _assert_common_no_p8_release_or_runtime_change(normalization)
    _assert_no_body_payload_key_like_values(normalization)


def test_r53_r11_ready_normalizes_24_bodyfree_rating_rows_without_question_or_reviewer_text() -> None:
    normalization = r53.build_p7_r53_rating_row_normalization_bodyfree(
        actual_human_review_result_capture=_r53_r10_ready(),
    )

    assert normalization["rating_row_normalizer_status"] == "READY_FOR_READFEEL_BLOCKER_EXECUTION_BLOCKER_INGESTION"
    assert normalization["review_session_status"] == "R53_RATING_ROW_NORMALIZATION_READY"
    assert normalization["r10_actual_review_capture_ready_for_rating_normalization"] is True
    assert normalization["r51_r9_next_required_step"] == r51.P7_R51_R9_NEXT_REQUIRED_STEP_REF
    assert normalization["rating_row_count"] == 24
    assert normalization["all_required_rating_rows_present"] is True
    assert normalization["rating_case_ref_sets_match_review_capture"] is True
    assert normalization["pass_requires_targets_and_no_blockers"] is True
    assert normalization["red_or_repair_requires_blocker"] is True
    assert normalization["actual_human_review_run_here"] is True
    assert normalization["actual_manual_review_run_here"] is True
    assert normalization["actual_rating_rows_materialized_here"] is True
    assert normalization["actual_blocker_rows_materialized_here"] is False
    assert normalization["actual_execution_blocker_rows_materialized_here"] is False
    assert normalization["actual_question_need_observation_rows_materialized_here"] is False
    assert normalization["p5_actual_review_still_not_run"] is False
    assert normalization["execution_blocker_ids"] == []
    assert normalization["r53_11_rating_row_normalization_built"] is True
    assert normalization["next_required_step"] == r53.P7_R53_R11_NEXT_REQUIRED_STEP_REF
    assert tuple(normalization["implemented_steps"]) == r53.P7_R53_R11_IMPLEMENTED_STEPS
    assert tuple(normalization["not_yet_implemented_steps"]) == r53.P7_R53_R11_NOT_YET_IMPLEMENTED_STEPS
    assert r51.assert_p7_r51_rating_row_normalizer_bodyfree_contract(
        normalization["r51_r9_rating_row_normalizer_bodyfree"],
        allowed_true_false_key_refs=r53.P7_R53_R11_ALLOWED_TRUE_FALSE_KEY_REFS,
    ) is True
    for row in normalization["rating_rows"]:  # type: ignore[index]
        assert isinstance(row, dict)
        assert row["schema_version"] == r51.P7_R51_RATING_ROW_BODYFREE_SCHEMA_VERSION
        assert row["body_free"] is True
        assert row["verdict"] == "PASS"
        assert row["blocker_ids"] == []
        assert row["reviewer_free_text_included"] is False
        assert row.get("question_text_included", False) is False
        assert row.get("draft_question_text_included", False) is False
        assert row.get("machine_auto_score_used", False) is False
        assert row.get("machine_metrics_used_for_readfeel", False) is False

    _assert_common_no_p8_release_or_runtime_change(normalization)
    _assert_no_body_payload_key_like_values(normalization)


@pytest.mark.parametrize(
    "key,value",
    [
        ("machine_auto_score_allowed", True),
        ("machine_metrics_used_for_readfeel_allowed", True),
        ("reviewer_free_text_bodyfree_allowed", True),
        ("actual_blocker_rows_materialized_here", True),
        ("actual_execution_blocker_rows_materialized_here", True),
        ("actual_question_need_observation_rows_materialized_here", True),
        ("actual_reviewer_notes_materialized_here", True),
        ("body_full_packet_generated_here", True),
        ("body_full_packets_created_local_only", True),
        ("p8_start_allowed", True),
        ("release_allowed", True),
        ("api_db_rn_response_key_changed_here", True),
        ("runtime_changed_here", True),
    ],
)
def test_r53_r11_rejects_machine_scoring_question_rows_bodyfull_or_release_promotion(key: str, value: object) -> None:
    normalization = r53.build_p7_r53_rating_row_normalization_bodyfree(
        actual_human_review_result_capture=_r53_r10_ready(),
    )
    normalization[key] = value
    with pytest.raises(ValueError):
        r53.assert_p7_r53_rating_row_normalization_bodyfree_contract(normalization)


def test_r53_r11_rejects_rating_row_that_contains_reviewer_or_question_text_flag() -> None:
    normalization = r53.build_p7_r53_rating_row_normalization_bodyfree(
        actual_human_review_result_capture=_r53_r10_ready(),
    )
    normalization["rating_rows"][0]["reviewer_free_text_included"] = True  # type: ignore[index]
    with pytest.raises(ValueError):
        r53.assert_p7_r53_rating_row_normalization_bodyfree_contract(normalization)
