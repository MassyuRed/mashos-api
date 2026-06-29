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
    '"question_api_implemented": true',
    '"question_db_schema_implemented": true',
    '"question_rn_ui_implemented": true',
    '"question_response_key_implemented": true',
    '"api_db_rn_response_key_changed_here": true',
    '"runtime_changed_here": true',
    '"actual_human_review_run_here": true',
    '"actual_manual_review_run_here": true',
    '"body_full_packet_generated_here": true',
    '"actual_body_full_packet_generated_here": true',
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
    return r54.build_p7_r54_local_only_actual_review_preflight_bodyfree(
        validation_evidence_intake=r54.build_p7_r54_validation_evidence_intake_bodyfree(),
        local_review_root=_ready_root(tmp_path),
        explicit_allow_token=r54.P7_R54_EXPLICIT_LOCAL_REVIEW_ALLOW_TOKEN_REF,
        purge_plan=r54.build_p7_r54_default_local_only_purge_plan_bodyfree(),
        export_candidate_refs=("bodyfree/result_handoff.json",),
    )


def _r5_ready(tmp_path) -> dict[str, object]:
    envelope = r54.build_p7_r54_actual_review_session_envelope_bodyfree(
        local_only_actual_review_preflight=_r3_ready(tmp_path),
    )
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
    form = r54.build_p7_r54_reviewer_instruction_rating_form_freeze_bodyfree(packet_completeness_export_denylist_scan=scan)
    assert form["instruction_form_status"] == "READY_FOR_ACTUAL_HUMAN_REVIEW_OPERATION_STATE_CAPTURE"
    return form


def _r9_capture_ready(tmp_path) -> dict[str, object]:
    return r54.build_p7_r54_actual_human_review_operation_state_capture_bodyfree(
        reviewer_instruction_rating_form_freeze=_r8_ready(tmp_path),
        review_operation_state_ref="review_completed_pending_sanitized_capture",
        reviewer_selection_count=24,
        reviewer_selection_source_ref="external_local_only_review_form_selection_count_only",
    )


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


def _r10_ready(tmp_path, rows: list[dict[str, object]] | None = None) -> dict[str, object]:
    manifest = _r5_ready(tmp_path)
    capture = r54.build_p7_r54_sanitized_actual_review_result_capture_bodyfree(
        actual_human_review_operation_state_capture=_r9_capture_ready(tmp_path),
        case_manifest_freeze=manifest,
        sanitized_review_result_rows=rows if rows is not None else _review_rows_from_manifest(manifest),
    )
    assert capture["capture_status"] == "READY_FOR_RATING_ROW_NORMALIZATION"
    return capture


def _r11_ready(tmp_path, capture: dict[str, object] | None = None) -> dict[str, object]:
    rating = r54.build_p7_r54_rating_row_normalization_bodyfree(
        sanitized_actual_review_result_capture=capture or _r10_ready(tmp_path),
    )
    assert rating["rating_row_normalizer_status"] == "READY_FOR_READFEEL_BLOCKER_EXECUTION_BLOCKER_INGESTION"
    return rating


def _r12_ready(tmp_path, rating: dict[str, object] | None = None) -> dict[str, object]:
    ingestion = r54.build_p7_r54_readfeel_blocker_execution_blocker_ingestion_bodyfree(
        rating_row_normalization=rating or _r11_ready(tmp_path),
    )
    assert ingestion["blocker_ingestion_status"] == "READY_FOR_QUESTION_NEED_OBSERVATION_ROW_NORMALIZATION"
    return ingestion


def _r13_ready(tmp_path, capture: dict[str, object] | None = None, rating: dict[str, object] | None = None) -> dict[str, object]:
    cap = capture or _r10_ready(tmp_path)
    rat = rating or _r11_ready(tmp_path, capture=cap)
    ingestion = _r12_ready(tmp_path, rating=rat)
    question = r54.build_p7_r54_question_need_observation_row_normalization_bodyfree(
        readfeel_blocker_execution_blocker_ingestion=ingestion,
        sanitized_actual_review_result_capture=cap,
    )
    assert question["question_observation_normalizer_status"] == "READY_FOR_RATING_QUESTION_OBSERVATION_CONSISTENCY_GUARD"
    return question


def _r14_ready(tmp_path, capture: dict[str, object] | None = None, rating: dict[str, object] | None = None) -> dict[str, object]:
    cap = capture or _r10_ready(tmp_path)
    rat = rating or _r11_ready(tmp_path, capture=cap)
    question = _r13_ready(tmp_path, capture=cap, rating=rat)
    guard = r54.build_p7_r54_rating_question_observation_consistency_guard_bodyfree(
        question_need_observation_row_normalization=question,
        rating_row_normalization=rat,
    )
    assert guard["rating_question_consistency_guard_status"] == "READY_FOR_PAUSE_ABORT_EXPIRATION_PROTOCOL"
    return guard


def _r15_ready(tmp_path, guard: dict[str, object] | None = None) -> dict[str, object]:
    protocol = r54.build_p7_r54_pause_abort_expiration_protocol_bodyfree(
        rating_question_observation_consistency_guard=guard or _r14_ready(tmp_path),
    )
    assert protocol["pause_abort_expiration_protocol_status"] == "READY_FOR_PURGE_DISPOSAL_RECEIPT"
    return protocol


def _purge_rows() -> list[dict[str, object]]:
    return [
        r54.build_p7_r54_purge_evidence_row_bodyfree(purge_target_ref=target_ref)
        for target_ref in r54.P7_R51_PURGE_PLAN_REQUIRED_DELETE_TARGET_REFS
    ]


def _ready_chain(tmp_path) -> tuple[dict[str, object], dict[str, object], dict[str, object], dict[str, object], dict[str, object], dict[str, object]]:
    capture = _r10_ready(tmp_path)
    rating = _r11_ready(tmp_path, capture=capture)
    blocker = _r12_ready(tmp_path, rating=rating)
    question = r54.build_p7_r54_question_need_observation_row_normalization_bodyfree(
        readfeel_blocker_execution_blocker_ingestion=blocker,
        sanitized_actual_review_result_capture=capture,
    )
    guard = r54.build_p7_r54_rating_question_observation_consistency_guard_bodyfree(
        question_need_observation_row_normalization=question,
        rating_row_normalization=rating,
    )
    protocol = _r15_ready(tmp_path, guard=guard)
    receipt = r54.build_p7_r54_purge_disposal_receipt_bodyfree(
        pause_abort_expiration_protocol=protocol,
        purge_evidence_rows=_purge_rows(),
    )
    return rating, blocker, question, guard, protocol, receipt


def test_r54_r16_default_blocks_until_r15_ready() -> None:
    receipt = r54.build_p7_r54_purge_disposal_receipt_bodyfree()

    assert set(receipt) == set(r54.P7_R54_PURGE_DISPOSAL_RECEIPT_REQUIRED_FIELD_REFS)
    assert receipt["schema_version"] == r54.P7_R54_PURGE_DISPOSAL_RECEIPT_SCHEMA_VERSION
    assert receipt["policy_section"] == r54.P7_R54_R16_STEP_REF
    assert receipt["purge_disposal_receipt_status"] == "BLOCKED_BY_R54_15_PAUSE_ABORT_EXPIRATION_PROTOCOL"
    assert receipt["r15_ready_for_purge_disposal_receipt"] is False
    assert receipt["disposal_verified"] is False
    assert receipt["disposal_failed"] is True
    assert receipt["disposal_receipt_materialized_here"] is False
    assert receipt["actual_disposal_receipt_materialized_here"] is False
    assert receipt["next_required_step"] == r54.P7_R54_R16_BLOCKED_NEXT_REQUIRED_STEP_REF

    assert r54.assert_p7_r54_purge_disposal_receipt_bodyfree_contract(receipt) is True
    _assert_body_free_no_runtime_promotion(receipt)


def test_r54_r16_ready_materializes_bodyfree_disposal_receipt_without_paths_or_hashes(tmp_path) -> None:
    receipt = r54.build_p7_r54_purge_disposal_receipt_bodyfree(
        pause_abort_expiration_protocol=_r15_ready(tmp_path),
        purge_evidence_rows=_purge_rows(),
    )

    assert receipt["review_session_status"] == "R54_PURGE_DISPOSAL_RECEIPT_VERIFIED_BODYFREE"
    assert receipt["purge_disposal_receipt_status"] == "READY_FOR_BODY_FREE_POST_REVIEW_SUMMARY"
    assert receipt["purge_evidence_row_count"] == len(r54.P7_R51_PURGE_PLAN_REQUIRED_DELETE_TARGET_REFS)
    assert receipt["verified_purge_target_count"] == receipt["purge_target_count"]
    assert receipt["missing_purge_target_refs"] == []
    assert receipt["failed_purge_target_refs"] == []
    assert receipt["disposal_verified"] is True
    assert receipt["body_removed"] is True
    assert receipt["reviewer_forms_removed"] is True
    assert receipt["reviewer_notes_removed"] is True
    assert receipt["local_packet_exported"] is False
    assert receipt["local_absolute_path_included"] is False
    assert receipt["body_content_hash_included"] is False
    assert receipt["packet_content_hash_included"] is False
    assert receipt["terminal_output_included"] is False
    assert receipt["local_file_delete_ops_executed_by_helper"] is False
    assert receipt["actual_disposal_run_here"] is False
    assert receipt["disposal_receipt_materialized_here"] is True
    assert receipt["actual_disposal_receipt_materialized_here"] is True
    assert receipt["post_review_summary_materialized_here"] is False
    assert tuple(receipt["implemented_steps"]) == r54.P7_R54_R16_IMPLEMENTED_STEPS
    assert tuple(receipt["not_yet_implemented_steps"]) == r54.P7_R54_R16_NOT_YET_IMPLEMENTED_STEPS
    assert receipt["next_required_step"] == r54.P7_R54_R16_NEXT_REQUIRED_STEP_REF

    assert r54.assert_p7_r54_purge_disposal_receipt_bodyfree_contract(receipt) is True
    _assert_body_free_no_runtime_promotion(receipt)


def test_r54_r16_blocks_if_any_required_purge_target_is_missing(tmp_path) -> None:
    partial_rows = _purge_rows()[:-1]
    receipt = r54.build_p7_r54_purge_disposal_receipt_bodyfree(
        pause_abort_expiration_protocol=_r15_ready(tmp_path),
        purge_evidence_rows=partial_rows,
    )

    assert receipt["purge_disposal_receipt_status"] == "BLOCKED_BY_BODY_FULL_PACKET_REVIEWER_NOTES_PURGE"
    assert receipt["disposal_verified"] is False
    assert receipt["missing_purge_target_refs"] == [r54.P7_R51_PURGE_PLAN_REQUIRED_DELETE_TARGET_REFS[-1]]
    assert receipt["actual_disposal_receipt_materialized_here"] is False
    assert receipt["next_required_step"] == r54.P7_R54_R16_BLOCKED_NEXT_REQUIRED_STEP_REF

    assert r54.assert_p7_r54_purge_disposal_receipt_bodyfree_contract(receipt) is True
    _assert_body_free_no_runtime_promotion(receipt)


def test_r54_r16_contract_rejects_path_hash_terminal_or_release_promotion(tmp_path) -> None:
    receipt = r54.build_p7_r54_purge_disposal_receipt_bodyfree(
        pause_abort_expiration_protocol=_r15_ready(tmp_path),
        purge_evidence_rows=_purge_rows(),
    )
    for key in (
        "local_packet_exported",
        "local_absolute_path_included",
        "body_content_hash_included",
        "packet_content_hash_included",
        "terminal_output_included",
        "actual_human_review_run_here",
        "p8_start_allowed",
        "release_allowed",
    ):
        mutated = deepcopy(receipt)
        mutated[key] = True
        with pytest.raises(ValueError):
            r54.assert_p7_r54_purge_disposal_receipt_bodyfree_contract(mutated)


def test_r54_r17_default_blocks_until_disposal_and_review_rows_are_ready() -> None:
    summary = r54.build_p7_r54_body_free_post_review_summary_bodyfree()

    assert set(summary) == set(r54.P7_R54_BODY_FREE_POST_REVIEW_SUMMARY_REQUIRED_FIELD_REFS)
    assert summary["schema_version"] == r54.P7_R54_BODY_FREE_POST_REVIEW_SUMMARY_SCHEMA_VERSION
    assert summary["policy_section"] == r54.P7_R54_R17_STEP_REF
    assert summary["post_review_summary_status"] == "BLOCKED_BY_POST_REVIEW_SUMMARY_REQUIREMENTS"
    assert summary["r16_ready_for_post_review_summary"] is False
    assert summary["all_24_cases_reviewed"] is False
    assert summary["body_free_summary_contains_only_counts_and_refs"] is False
    assert summary["actual_review_run_here"] is False
    assert summary["post_review_summary_materialized_here"] is False
    assert summary["next_required_step"] == r54.P7_R54_R17_BLOCKED_NEXT_REQUIRED_STEP_REF

    assert r54.assert_p7_r54_body_free_post_review_summary_bodyfree_contract(summary) is True
    _assert_body_free_no_runtime_promotion(summary)


def test_r54_r17_ready_summarizes_counts_refs_only_without_p5_p6_p8_release_promotion(tmp_path) -> None:
    rating, blocker, question, guard, _protocol, receipt = _ready_chain(tmp_path)
    summary = r54.build_p7_r54_body_free_post_review_summary_bodyfree(
        purge_disposal_receipt=receipt,
        rating_row_normalization=rating,
        readfeel_blocker_execution_blocker_ingestion=blocker,
        question_need_observation_row_normalization=question,
        rating_question_observation_consistency_guard=guard,
    )

    assert summary["review_session_status"] == "R54_BODY_FREE_POST_REVIEW_SUMMARY_READY"
    assert summary["post_review_summary_status"] == "READY_FOR_P5_DECISION_CANDIDATE_SEPARATION"
    assert summary["body_free_summary_contains_only_counts_and_refs"] is True
    assert summary["summary_contains_rating_rows"] is False
    assert summary["summary_contains_question_observation_rows"] is False
    assert summary["summary_contains_review_body_rows"] is False
    assert "rating_rows" not in summary
    assert "question_need_observation_rows" not in summary
    assert summary["all_24_cases_reviewed"] is True
    assert summary["rating_row_count"] == 24
    assert summary["question_observation_row_count"] == 24
    assert summary["verdict_counts"] == {"PASS": 24, "YELLOW": 0, "REPAIR_REQUIRED": 0, "RED": 0}
    assert set(summary["axis_score_averages"]) == set(r54.P5_HUMAN_BLIND_QA_RATING_AXES)
    assert summary["all_axis_targets_met"] is True
    assert summary["disposal_verified"] is True
    assert summary["body_removed"] is True
    assert summary["reviewer_notes_removed"] is True
    assert summary["actual_review_run_here"] is True
    assert summary["actual_human_review_run_here"] is False
    assert summary["actual_manual_review_run_here"] is False
    assert summary["actual_question_need_observation_summary_materialized_here"] is True
    assert summary["post_review_summary_materialized_here"] is True
    assert summary["p5_confirmed_requirements_met_by_summary"] is True
    assert summary["p5_human_blind_qa_confirmed_candidate"] is False
    assert summary["p6_limited_human_readfeel_start_allowed"] is False
    assert summary["p8_start_allowed"] is False
    assert summary["release_allowed"] is False
    assert tuple(summary["implemented_steps"]) == r54.P7_R54_R17_IMPLEMENTED_STEPS
    assert tuple(summary["not_yet_implemented_steps"]) == r54.P7_R54_R17_NOT_YET_IMPLEMENTED_STEPS
    assert summary["next_required_step"] == r54.P7_R54_R17_NEXT_REQUIRED_STEP_REF

    assert r54.assert_p7_r54_body_free_post_review_summary_bodyfree_contract(summary) is True
    _assert_body_free_no_runtime_promotion(summary)


def test_r54_r17_blocks_if_disposal_receipt_is_not_verified(tmp_path) -> None:
    rating, blocker, question, guard, _protocol, receipt = _ready_chain(tmp_path)
    blocked_receipt = deepcopy(receipt)
    blocked_receipt["purge_disposal_receipt_status"] = "BLOCKED_BY_DISPOSAL_RECEIPT_VERIFICATION"
    blocked_receipt["disposal_verified"] = False
    blocked_receipt["disposal_failed"] = True
    blocked_receipt["summary_finalize_allowed"] = False
    blocked_receipt["body_removed"] = False
    blocked_receipt["reviewer_forms_removed"] = False
    blocked_receipt["reviewer_notes_removed"] = False
    blocked_receipt["body_full_packets_removed"] = False
    blocked_receipt["disposal_receipt_materialized_here"] = False
    blocked_receipt["actual_disposal_receipt_materialized_here"] = False
    blocked_receipt["r54_16_purge_disposal_receipt_built"] = False
    blocked_receipt["execution_blocker_ids"] = ["r54_disposal_not_verified_before_summary"]
    blocked_receipt["open_execution_blocker_ids"] = ["r54_disposal_not_verified_before_summary"]
    blocked_receipt["next_required_step"] = r54.P7_R54_R16_BLOCKED_NEXT_REQUIRED_STEP_REF

    # The mutated receipt is intentionally not a valid R16 material, so build a valid blocked one instead.
    blocked = r54.build_p7_r54_purge_disposal_receipt_bodyfree(
        pause_abort_expiration_protocol=_r15_ready(tmp_path),
        purge_evidence_rows=_purge_rows()[:-1],
    )
    summary = r54.build_p7_r54_body_free_post_review_summary_bodyfree(
        purge_disposal_receipt=blocked,
        rating_row_normalization=rating,
        readfeel_blocker_execution_blocker_ingestion=blocker,
        question_need_observation_row_normalization=question,
        rating_question_observation_consistency_guard=guard,
    )

    assert summary["post_review_summary_status"] == "BLOCKED_BY_POST_REVIEW_SUMMARY_REQUIREMENTS"
    assert summary["r16_ready_for_post_review_summary"] is False
    assert "r54_disposal_not_verified_before_summary" in summary["execution_blocker_ids"]
    assert summary["post_review_summary_materialized_here"] is False
    assert summary["actual_review_run_here"] is False
    assert summary["next_required_step"] == r54.P7_R54_R17_BLOCKED_NEXT_REQUIRED_STEP_REF

    assert r54.assert_p7_r54_body_free_post_review_summary_bodyfree_contract(summary) is True
    _assert_body_free_no_runtime_promotion(summary)


def test_r54_r17_contract_rejects_rows_body_leak_promotion_or_human_review_claim(tmp_path) -> None:
    rating, blocker, question, guard, _protocol, receipt = _ready_chain(tmp_path)
    summary = r54.build_p7_r54_body_free_post_review_summary_bodyfree(
        purge_disposal_receipt=receipt,
        rating_row_normalization=rating,
        readfeel_blocker_execution_blocker_ingestion=blocker,
        question_need_observation_row_normalization=question,
        rating_question_observation_consistency_guard=guard,
    )
    mutations: list[tuple[str, object]] = [
        ("summary_contains_rating_rows", True),
        ("summary_contains_question_observation_rows", True),
        ("actual_human_review_run_here", True),
        ("p5_human_blind_qa_confirmed_candidate", True),
        ("p6_limited_human_readfeel_start_allowed", True),
        ("p8_start_allowed", True),
        ("release_allowed", True),
        ("local_absolute_path_included", True),
        ("body_content_hash_included", True),
    ]
    for key, value in mutations:
        mutated = deepcopy(summary)
        mutated[key] = value
        with pytest.raises(ValueError):
            r54.assert_p7_r54_body_free_post_review_summary_bodyfree_contract(mutated)

    leaked = deepcopy(summary)
    leaked["rating_rows"] = rating["rating_rows"]
    with pytest.raises(ValueError):
        r54.assert_p7_r54_body_free_post_review_summary_bodyfree_contract(leaked)
