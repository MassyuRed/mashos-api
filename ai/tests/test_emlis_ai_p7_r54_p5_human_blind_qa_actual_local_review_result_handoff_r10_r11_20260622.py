# -*- coding: utf-8 -*-
from __future__ import annotations

import json
import uuid
from copy import deepcopy

import pytest

import emlis_ai_p7_r54_p5_human_blind_qa_actual_local_review_result_handoff as r54


FORBIDDEN_BODY_TOKENS = (
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
FORBIDDEN_RUNTIME_PROMOTION_TRUE_TOKENS = (
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
    '"actual_question_need_observation_rows_materialized_here": true',
    '"actual_disposal_receipt_materialized_here": true',
    '"p5_human_blind_qa_confirmed_candidate": true',
)


def _assert_body_free_no_runtime_promotion(material: dict[str, object]) -> None:
    dumped = json.dumps(material, ensure_ascii=False, sort_keys=True).lower()
    for forbidden in FORBIDDEN_BODY_TOKENS:
        assert forbidden not in dumped
    for forbidden in FORBIDDEN_RUNTIME_PROMOTION_TRUE_TOKENS:
        assert forbidden not in dumped


def _ready_root(tmp_path) -> str:
    root = tmp_path / f"r54_external_local_review_root_{uuid.uuid4().hex}"
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


def _r5_ready(tmp_path) -> dict[str, object]:
    envelope = r54.build_p7_r54_actual_review_session_envelope_bodyfree(
        local_only_actual_review_preflight=_r3_ready(tmp_path),
    )
    assert envelope["envelope_status"] == "READY_FOR_24_CASE_MANIFEST_FREEZE"
    manifest = r54.build_p7_r54_24_case_manifest_freeze_bodyfree(actual_review_session_envelope=envelope)
    assert manifest["manifest_status"] == "READY_FOR_LOCAL_ONLY_PACKET_GENERATION_REQUEST"
    return manifest


def _r8_ready(tmp_path) -> dict[str, object]:
    manifest = _r5_ready(tmp_path)
    request = r54.build_p7_r54_local_only_body_full_packet_generation_request_bodyfree(case_manifest_freeze=manifest)
    completion_rows = [
        r54.build_p7_r54_packet_completion_scan_row_bodyfree(
            blind_case_id=row["blind_case_id"],
            packet_ref_id=row["packet_ref_id"],
            index=index,
        )
        for index, row in enumerate(request["packet_generation_request_rows"], start=1)
    ]
    scan = r54.build_p7_r54_packet_completeness_export_denylist_scan_bodyfree(
        packet_generation_request=request,
        packet_completion_rows=completion_rows,
        export_candidate_refs=("bodyfree/result_handoff.json", "bodyfree/disposal_receipt.json"),
    )
    assert scan["packet_completeness_scan_status"] == "R54_PACKET_COMPLETENESS_EXPORT_DENYLIST_SCAN_READY"
    form = r54.build_p7_r54_reviewer_instruction_rating_form_freeze_bodyfree(packet_completeness_export_denylist_scan=scan)
    assert form["instruction_form_status"] == "READY_FOR_ACTUAL_HUMAN_REVIEW_OPERATION_STATE_CAPTURE"
    return form


def _r9_capture_ready(tmp_path) -> dict[str, object]:
    state = r54.build_p7_r54_actual_human_review_operation_state_capture_bodyfree(
        reviewer_instruction_rating_form_freeze=_r8_ready(tmp_path),
        review_operation_state_ref="review_completed_pending_sanitized_capture",
        reviewer_selection_count=24,
        reviewer_selection_source_ref="external_local_only_review_form_selection_count_only",
    )
    assert state["operation_state_capture_status"] == "READY_FOR_SANITIZED_ACTUAL_REVIEW_RESULT_CAPTURE"
    return state


def _subscription_boundary(row: dict[str, object]) -> str:
    return "free_history_not_allowed" if row["subscription_tier_ref"] == "free" else "plus_or_premium_history_allowed"


def _review_rows_from_manifest(manifest: dict[str, object]) -> list[dict[str, object]]:
    return [
        r54.build_p7_r54_sanitized_review_result_row_bodyfree(
            blind_case_id=row["blind_case_id"],
            case_ref_id=row["case_ref_id"],
            packet_ref_id=row["packet_ref_id"],
            case_family_ref=row["family"],
            case_role_ref=row["case_role"],
            subscription_boundary_ref=_subscription_boundary(row),
        )
        for row in manifest["controller_manifest_rows"]
    ]


def _r10_ready(tmp_path) -> dict[str, object]:
    manifest = _r5_ready(tmp_path)
    capture = r54.build_p7_r54_sanitized_actual_review_result_capture_bodyfree(
        actual_human_review_operation_state_capture=_r9_capture_ready(tmp_path),
        case_manifest_freeze=manifest,
        sanitized_review_result_rows=_review_rows_from_manifest(manifest),
    )
    assert capture["capture_status"] == "READY_FOR_RATING_ROW_NORMALIZATION"
    return capture


def test_r54_r10_blocks_by_default_before_r9_capture_ready() -> None:
    capture = r54.build_p7_r54_sanitized_actual_review_result_capture_bodyfree()

    assert set(capture) == set(r54.P7_R54_SANITIZED_ACTUAL_REVIEW_RESULT_CAPTURE_REQUIRED_FIELD_REFS)
    assert capture["schema_version"] == r54.P7_R54_SANITIZED_ACTUAL_REVIEW_RESULT_CAPTURE_SCHEMA_VERSION
    assert capture["policy_section"] == r54.P7_R54_R10_STEP_REF
    assert capture["capture_status"] == "BLOCKED_BY_R54_9_OR_MISSING_SANITIZED_REVIEW_RESULTS"
    assert capture["r9_ready_for_sanitized_actual_review_result_capture"] is False
    assert capture["sanitized_review_result_row_count"] == 0
    assert capture["sanitized_review_result_rows"] == []
    assert capture["actual_review_result_rows_captured_here"] is False
    assert capture["actual_human_review_run_here"] is False
    assert capture["actual_rating_rows_materialized_here"] is False
    assert "r54_sanitized_review_operation_state_not_ready" in capture["execution_blocker_ids"]
    assert capture["next_required_step"] == r54.P7_R54_R10_BLOCKED_NEXT_REQUIRED_STEP_REF

    assert r54.assert_p7_r54_sanitized_actual_review_result_capture_bodyfree_contract(capture) is True
    _assert_body_free_no_runtime_promotion(capture)


def test_r54_r10_ready_captures_24_sanitized_review_rows_bodyfree(tmp_path) -> None:
    manifest = _r5_ready(tmp_path)
    capture = r54.build_p7_r54_sanitized_actual_review_result_capture_bodyfree(
        actual_human_review_operation_state_capture=_r9_capture_ready(tmp_path),
        case_manifest_freeze=manifest,
        sanitized_review_result_rows=_review_rows_from_manifest(manifest),
    )

    assert capture["capture_status"] == "READY_FOR_RATING_ROW_NORMALIZATION"
    assert capture["r9_ready_for_sanitized_actual_review_result_capture"] is True
    assert capture["r5_manifest_ready_for_result_capture"] is True
    assert capture["sanitized_review_result_row_count"] == 24
    assert capture["reviewed_blind_case_id_count"] == 24
    assert capture["reviewed_case_ref_id_count"] == 24
    assert capture["reviewed_packet_ref_id_count"] == 24
    assert capture["review_result_case_set_matches_manifest"] is True
    assert capture["all_24_cases_reviewed"] is True
    assert capture["rating_selections_captured_bodyfree"] is True
    assert capture["question_need_observation_selections_captured_bodyfree"] is True
    assert capture["actual_review_result_rows_captured_here"] is True
    assert capture["actual_human_review_run_here"] is False
    assert capture["actual_rating_rows_materialized_here"] is False
    assert capture["raw_input_included"] is False
    assert capture["returned_surface_included"] is False
    assert capture["comment_text_included"] is False
    assert capture["history_body_included"] is False
    assert capture["question_text_included"] is False
    assert capture["draft_question_text_included"] is False
    assert capture["body_content_hash_included"] is False
    assert capture["local_absolute_path_included"] is False
    assert capture["execution_blocker_ids"] == []
    assert tuple(capture["implemented_steps"]) == r54.P7_R54_R10_IMPLEMENTED_STEPS
    assert tuple(capture["not_yet_implemented_steps"]) == r54.P7_R54_R10_NOT_YET_IMPLEMENTED_STEPS
    assert capture["next_required_step"] == r54.P7_R54_R10_NEXT_REQUIRED_STEP_REF

    first = capture["sanitized_review_result_rows"][0]
    assert set(first) == set(r54.P7_R54_SANITIZED_REVIEW_RESULT_ROW_REQUIRED_FIELD_REFS)
    assert first["machine_auto_score_used"] is False
    assert first["question_text_included"] is False
    assert first["body_free"] is True

    assert r54.assert_p7_r54_sanitized_actual_review_result_capture_bodyfree_contract(capture) is True
    _assert_body_free_no_runtime_promotion(capture)


def test_r54_r10_blocks_partial_row_set_without_exposing_partial_rows(tmp_path) -> None:
    manifest = _r5_ready(tmp_path)
    capture = r54.build_p7_r54_sanitized_actual_review_result_capture_bodyfree(
        actual_human_review_operation_state_capture=_r9_capture_ready(tmp_path),
        case_manifest_freeze=manifest,
        sanitized_review_result_rows=_review_rows_from_manifest(manifest)[:23],
    )

    assert capture["capture_status"] == "BLOCKED_BY_R54_9_OR_MISSING_SANITIZED_REVIEW_RESULTS"
    assert capture["sanitized_review_result_row_count"] == 0
    assert capture["sanitized_review_result_rows"] == []
    assert capture["actual_review_result_rows_captured_here"] is False
    assert "r54_sanitized_review_result_rows_incomplete" in capture["execution_blocker_ids"]
    assert r54.assert_p7_r54_sanitized_actual_review_result_capture_bodyfree_contract(capture) is True


def test_r54_r10_rejects_body_hash_question_or_local_path_payload_in_rows(tmp_path) -> None:
    manifest = _r5_ready(tmp_path)
    rows = _review_rows_from_manifest(manifest)
    rows[0] = deepcopy(rows[0])
    rows[0]["body_content_hash"] = "must_not_export_hash"

    with pytest.raises(ValueError):
        r54.build_p7_r54_sanitized_actual_review_result_capture_bodyfree(
            actual_human_review_operation_state_capture=_r9_capture_ready(tmp_path),
            case_manifest_freeze=manifest,
            sanitized_review_result_rows=rows,
        )


def test_r54_r11_blocks_without_r10_ready_capture() -> None:
    normalization = r54.build_p7_r54_rating_row_normalization_bodyfree()

    assert set(normalization) == set(r54.P7_R54_RATING_ROW_NORMALIZATION_REQUIRED_FIELD_REFS)
    assert normalization["schema_version"] == r54.P7_R54_RATING_ROW_NORMALIZATION_SCHEMA_VERSION
    assert normalization["policy_section"] == r54.P7_R54_R11_STEP_REF
    assert normalization["rating_row_normalizer_status"] == "BLOCKED_BY_R54_10_SANITIZED_CAPTURE"
    assert normalization["r10_capture_ready_for_rating_normalization"] is False
    assert normalization["rating_row_count"] == 0
    assert normalization["rating_rows"] == []
    assert normalization["actual_rating_rows_materialized_here"] is False
    assert "r54_rating_row_normalization_capture_not_ready" in normalization["execution_blocker_ids"]
    assert normalization["next_required_step"] == r54.P7_R54_R11_BLOCKED_NEXT_REQUIRED_STEP_REF

    assert r54.assert_p7_r54_rating_row_normalization_bodyfree_contract(normalization) is True
    _assert_body_free_no_runtime_promotion(normalization)


def test_r54_r11_ready_normalizes_24_rating_rows_and_keeps_runtime_boundaries(tmp_path) -> None:
    normalization = r54.build_p7_r54_rating_row_normalization_bodyfree(
        sanitized_actual_review_result_capture=_r10_ready(tmp_path),
    )

    assert normalization["rating_row_normalizer_status"] == "READY_FOR_READFEEL_BLOCKER_EXECUTION_BLOCKER_INGESTION"
    assert normalization["r10_capture_ready_for_rating_normalization"] is True
    assert normalization["sanitized_review_result_row_count"] == 24
    assert normalization["rating_row_count"] == 24
    assert len(normalization["rating_rows"]) == 24
    assert tuple(normalization["rating_axis_refs"]) == r54.P5_HUMAN_BLIND_QA_RATING_AXES
    assert normalization["missing_axis_scores_pass_allowed"] is False
    assert normalization["extra_rating_axis_allowed"] is False
    assert normalization["machine_auto_score_allowed"] is False
    assert normalization["machine_metrics_used_for_readfeel_allowed"] is False
    assert normalization["reviewer_free_text_bodyfree_allowed"] is False
    assert normalization["rating_rows_are_bodyfree"] is True
    assert normalization["all_required_rating_rows_present"] is True
    assert normalization["rating_case_ref_sets_match_review_capture"] is True
    assert normalization["verdict_counts"]["PASS"] == 24
    assert normalization["rating_consistency_issue_count"] == 0
    assert normalization["pass_with_critical_blocker_detected"] is False
    assert normalization["actual_rating_rows_materialized_here"] is True
    assert normalization["actual_human_review_run_here"] is False
    assert normalization["actual_manual_review_run_here"] is False
    assert normalization["actual_question_need_observation_rows_materialized_here"] is False
    assert normalization["execution_blocker_ids"] == []
    assert tuple(normalization["implemented_steps"]) == r54.P7_R54_R11_IMPLEMENTED_STEPS
    assert tuple(normalization["not_yet_implemented_steps"]) == r54.P7_R54_R11_NOT_YET_IMPLEMENTED_STEPS
    assert normalization["next_required_step"] == r54.P7_R54_R11_NEXT_REQUIRED_STEP_REF

    first = normalization["rating_rows"][0]
    assert set(first) == set(r54.P7_R54_RATING_ROW_BODYFREE_REQUIRED_FIELD_REFS)
    assert set(first["axis_scores"]) == set(r54.P5_HUMAN_BLIND_QA_RATING_AXES)
    assert first["machine_auto_score_used"] is False
    assert first["reviewer_free_text_included"] is False
    assert first["question_text_included"] is False
    assert first["body_free"] is True

    assert r54.assert_p7_r54_rating_row_normalization_bodyfree_contract(normalization) is True
    _assert_body_free_no_runtime_promotion(normalization)


def test_r54_r11_detects_pass_with_critical_blocker_as_consistency_issue(tmp_path) -> None:
    manifest = _r5_ready(tmp_path)
    rows = _review_rows_from_manifest(manifest)
    first = manifest["controller_manifest_rows"][0]
    rows[0] = r54.build_p7_r54_sanitized_review_result_row_bodyfree(
        blind_case_id=first["blind_case_id"],
        case_ref_id=first["case_ref_id"],
        packet_ref_id=first["packet_ref_id"],
        case_family_ref=first["family"],
        case_role_ref=first["case_role"],
        subscription_boundary_ref=_subscription_boundary(first),
        verdict="PASS",
        readfeel_blocker_ids=("p5_history_scope_overclaim",),
    )
    capture = r54.build_p7_r54_sanitized_actual_review_result_capture_bodyfree(
        actual_human_review_operation_state_capture=_r9_capture_ready(tmp_path),
        case_manifest_freeze=manifest,
        sanitized_review_result_rows=rows,
    )
    normalization = r54.build_p7_r54_rating_row_normalization_bodyfree(
        sanitized_actual_review_result_capture=capture,
    )

    assert normalization["rating_row_normalizer_status"] == "READY_FOR_READFEEL_BLOCKER_EXECUTION_BLOCKER_INGESTION"
    assert normalization["pass_with_critical_blocker_detected"] is True
    assert normalization["pass_with_any_blocker_detected"] is True
    assert normalization["rating_consistency_issue_count"] >= 2
    assert {row["issue_id"] for row in normalization["rating_consistency_issue_rows"]} >= {
        "r54_pass_with_critical_blocker_detected",
        "r54_pass_with_any_blocker_detected",
    }
    assert r54.assert_p7_r54_rating_row_normalization_bodyfree_contract(normalization) is True


@pytest.mark.parametrize(
    "key,value",
    [
        ("machine_auto_score_allowed", True),
        ("machine_metrics_used_for_readfeel_allowed", True),
        ("reviewer_free_text_bodyfree_allowed", True),
        ("actual_human_review_run_here", True),
        ("actual_manual_review_run_here", True),
        ("actual_question_need_observation_rows_materialized_here", True),
        ("p8_start_allowed", True),
        ("release_allowed", True),
    ],
)
def test_r54_r11_rejects_machine_free_text_review_run_or_promotion_mutations(tmp_path, key: str, value: object) -> None:
    normalization = r54.build_p7_r54_rating_row_normalization_bodyfree(
        sanitized_actual_review_result_capture=_r10_ready(tmp_path),
    )
    normalization[key] = value
    with pytest.raises(ValueError):
        r54.assert_p7_r54_rating_row_normalization_bodyfree_contract(normalization)


def test_r54_r11_rejects_rating_row_missing_axis_mutation(tmp_path) -> None:
    normalization = r54.build_p7_r54_rating_row_normalization_bodyfree(
        sanitized_actual_review_result_capture=_r10_ready(tmp_path),
    )
    normalization["rating_rows"][0] = deepcopy(normalization["rating_rows"][0])
    del normalization["rating_rows"][0]["axis_scores"][r54.P5_HUMAN_BLIND_QA_RATING_AXES[0]]

    with pytest.raises(ValueError):
        r54.assert_p7_r54_rating_row_normalization_bodyfree_contract(normalization)
