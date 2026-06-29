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
    '"p5_human_blind_qa_confirmed_final": true',
    '"p5_decision_finalized_here": true',
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


def _review_row_from_manifest_row(row: dict[str, object], **overrides: object) -> dict[str, object]:
    kwargs: dict[str, object] = {
        "blind_case_id": row["blind_case_id"],
        "case_ref_id": row["case_ref_id"],
        "packet_ref_id": row["packet_ref_id"],
        "case_family_ref": row["family"],
        "case_role_ref": row["case_role"],
        "subscription_boundary_ref": _subscription_boundary(row),
    }
    kwargs.update(overrides)
    return r54.build_p7_r54_sanitized_review_result_row_bodyfree(**kwargs)


def _review_rows_from_manifest(manifest: dict[str, object]) -> list[dict[str, object]]:
    return [
        _review_row_from_manifest_row(row)
        for row in manifest["controller_manifest_rows"]
    ]


def _r10_ready_from_rows(tmp_path, rows: list[dict[str, object]] | None = None) -> dict[str, object]:
    manifest = _r5_ready(tmp_path)
    capture = r54.build_p7_r54_sanitized_actual_review_result_capture_bodyfree(
        actual_human_review_operation_state_capture=_r9_capture_ready(tmp_path),
        case_manifest_freeze=manifest,
        sanitized_review_result_rows=rows if rows is not None else _review_rows_from_manifest(manifest),
    )
    assert capture["capture_status"] == "READY_FOR_RATING_ROW_NORMALIZATION"
    return capture


def _r10_ready_with_transform(tmp_path, transform=None) -> dict[str, object]:
    manifest = _r5_ready(tmp_path)
    rows = _review_rows_from_manifest(manifest)
    if transform is not None:
        rows = transform(rows, manifest)
    capture = r54.build_p7_r54_sanitized_actual_review_result_capture_bodyfree(
        actual_human_review_operation_state_capture=_r9_capture_ready(tmp_path),
        case_manifest_freeze=manifest,
        sanitized_review_result_rows=rows,
    )
    assert capture["capture_status"] == "READY_FOR_RATING_ROW_NORMALIZATION"
    return capture


def _purge_rows() -> list[dict[str, object]]:
    return [
        r54.build_p7_r54_purge_evidence_row_bodyfree(purge_target_ref=target_ref)
        for target_ref in r54.P7_R51_PURGE_PLAN_REQUIRED_DELETE_TARGET_REFS
    ]


def _summary_from_capture(tmp_path, capture: dict[str, object]) -> dict[str, object]:
    rating = r54.build_p7_r54_rating_row_normalization_bodyfree(
        sanitized_actual_review_result_capture=capture,
    )
    blocker = r54.build_p7_r54_readfeel_blocker_execution_blocker_ingestion_bodyfree(
        rating_row_normalization=rating,
    )
    question = r54.build_p7_r54_question_need_observation_row_normalization_bodyfree(
        readfeel_blocker_execution_blocker_ingestion=blocker,
        sanitized_actual_review_result_capture=capture,
    )
    guard = r54.build_p7_r54_rating_question_observation_consistency_guard_bodyfree(
        question_need_observation_row_normalization=question,
        rating_row_normalization=rating,
    )
    protocol = r54.build_p7_r54_pause_abort_expiration_protocol_bodyfree(
        rating_question_observation_consistency_guard=guard,
    )
    receipt = r54.build_p7_r54_purge_disposal_receipt_bodyfree(
        pause_abort_expiration_protocol=protocol,
        purge_evidence_rows=_purge_rows(),
    )
    summary = r54.build_p7_r54_body_free_post_review_summary_bodyfree(
        purge_disposal_receipt=receipt,
        rating_row_normalization=rating,
        readfeel_blocker_execution_blocker_ingestion=blocker,
        question_need_observation_row_normalization=question,
        rating_question_observation_consistency_guard=guard,
    )
    return summary


def _ready_summary(tmp_path) -> dict[str, object]:
    return _summary_from_capture(tmp_path, _r10_ready_from_rows(tmp_path))


def _repair_summary(tmp_path) -> dict[str, object]:
    def transform(rows: list[dict[str, object]], manifest: dict[str, object]) -> list[dict[str, object]]:
        updated = list(rows)
        source = manifest["controller_manifest_rows"][0]
        updated[0] = _review_row_from_manifest_row(
            source,
            verdict="REPAIR_REQUIRED",
            readfeel_blocker_ids=("p5_history_connection_too_generic",),
            question_need_primary_class="not_question_p5_surface_repair_required",
            one_question_fit_ref="repair_required_not_question",
            repair_required_refs=("p5_surface_repair_required",),
        )
        return updated

    return _summary_from_capture(tmp_path, _r10_ready_with_transform(tmp_path, transform=transform))


def _yellow_summary(tmp_path) -> dict[str, object]:
    def transform(rows: list[dict[str, object]], manifest: dict[str, object]) -> list[dict[str, object]]:
        updated = list(rows)
        source = manifest["controller_manifest_rows"][0]
        updated[0] = _review_row_from_manifest_row(source, verdict="YELLOW")
        return updated

    return _summary_from_capture(tmp_path, _r10_ready_with_transform(tmp_path, transform=transform))


def test_r54_r18_default_blocks_until_r17_summary_is_ready() -> None:
    decision = r54.build_p7_r54_p5_decision_candidate_separation_bodyfree()

    assert set(decision) == set(r54.P7_R54_P5_DECISION_CANDIDATE_SEPARATION_REQUIRED_FIELD_REFS)
    assert decision["schema_version"] == r54.P7_R54_P5_DECISION_CANDIDATE_SEPARATION_SCHEMA_VERSION
    assert decision["policy_section"] == r54.P7_R54_R18_STEP_REF
    assert decision["p5_decision_candidate_status"] == "BLOCKED_BY_R54_17_BODY_FREE_POST_REVIEW_SUMMARY"
    assert decision["p5_decision_candidate_ref"] == "P5_NOT_REVIEWED"
    assert decision["p5_decision_candidate_materialized_here"] is False
    assert decision["r54_18_p5_decision_candidate_separation_built"] is False
    assert decision["p5_human_blind_qa_confirmed_candidate"] is False
    assert decision["p5_human_blind_qa_confirmed_final"] is False
    assert decision["p6_limited_human_readfeel_start_allowed"] is False
    assert decision["p8_start_allowed"] is False
    assert decision["next_required_step"] == r54.P7_R54_R18_BLOCKED_NEXT_REQUIRED_STEP_REF

    assert r54.assert_p7_r54_p5_decision_candidate_separation_bodyfree_contract(decision) is True
    _assert_body_free_no_runtime_promotion(decision)


def test_r54_r18_confirmed_candidate_only_after_clean_24_case_summary_not_final(tmp_path) -> None:
    decision = r54.build_p7_r54_p5_decision_candidate_separation_bodyfree(
        body_free_post_review_summary=_ready_summary(tmp_path),
    )

    assert decision["p5_decision_candidate_status"] == "P5_CONFIRMED_CANDIDATE_SEPARATED"
    assert decision["p5_decision_candidate_ref"] == "P5_CONFIRMED_CANDIDATE"
    assert decision["confirmed_candidate_requirements_met"] is True
    assert decision["p5_human_blind_qa_confirmed_candidate"] is True
    assert decision["p5_human_blind_qa_confirmed_final"] is False
    assert decision["p5_repair_return_candidate"] is False
    assert decision["p5_review_inconclusive"] is False
    assert decision["p6_limited_human_readfeel_candidate"] is False
    assert decision["p6_limited_human_readfeel_start_allowed"] is False
    assert decision["p8_start_allowed"] is False
    assert decision["release_allowed"] is False
    assert decision["next_required_step"] == r54.P7_R54_R18_NEXT_REQUIRED_STEP_REF

    assert r54.assert_p7_r54_p5_decision_candidate_separation_bodyfree_contract(decision) is True
    _assert_body_free_no_runtime_promotion(decision)


def test_r54_r18_routes_red_or_repair_and_not_question_repair_to_p5_repair_return(tmp_path) -> None:
    decision = r54.build_p7_r54_p5_decision_candidate_separation_bodyfree(
        body_free_post_review_summary=_repair_summary(tmp_path),
    )

    assert decision["p5_decision_candidate_status"] == "P5_REPAIR_RETURN_CANDIDATE_SEPARATED"
    assert decision["p5_decision_candidate_ref"] == "P5_REPAIR_RETURN"
    assert decision["p5_repair_return_candidate"] is True
    assert decision["p5_human_blind_qa_confirmed_candidate"] is False
    assert decision["p5_review_inconclusive"] is False
    assert decision["repair_return_required"] is True
    assert "r54_p5_repair_return_required_by_not_question_repair_observation" in decision["p5_decision_reason_refs"]
    assert decision["p6_limited_human_readfeel_start_allowed"] is False
    assert decision["p8_start_allowed"] is False

    assert r54.assert_p7_r54_p5_decision_candidate_separation_bodyfree_contract(decision) is True
    _assert_body_free_no_runtime_promotion(decision)


def test_r54_r18_keeps_yellow_summary_inconclusive_not_confirmed(tmp_path) -> None:
    decision = r54.build_p7_r54_p5_decision_candidate_separation_bodyfree(
        body_free_post_review_summary=_yellow_summary(tmp_path),
    )

    assert decision["p5_decision_candidate_status"] == "P5_INCONCLUSIVE_CANDIDATE_SEPARATED"
    assert decision["p5_decision_candidate_ref"] == "P5_INCONCLUSIVE_YELLOW_REQUIRES_HUMAN_DECISION"
    assert decision["p5_review_inconclusive"] is True
    assert decision["p5_human_blind_qa_confirmed_candidate"] is False
    assert decision["p5_repair_return_candidate"] is False
    assert decision["p5_human_blind_qa_confirmed_final"] is False
    assert decision["p6_limited_human_readfeel_start_allowed"] is False

    assert r54.assert_p7_r54_p5_decision_candidate_separation_bodyfree_contract(decision) is True
    _assert_body_free_no_runtime_promotion(decision)


def test_r54_r18_contract_rejects_final_start_or_release_promotion(tmp_path) -> None:
    decision = r54.build_p7_r54_p5_decision_candidate_separation_bodyfree(
        body_free_post_review_summary=_ready_summary(tmp_path),
    )
    for key in (
        "p5_human_blind_qa_confirmed_final",
        "p5_decision_finalized_here",
        "p6_limited_human_readfeel_start_allowed",
        "p8_start_allowed",
        "p7_complete",
        "release_allowed",
        "actual_human_review_run_here",
        "actual_manual_review_run_here",
        "local_absolute_path_included",
        "body_content_hash_included",
    ):
        mutated = deepcopy(decision)
        mutated[key] = True
        with pytest.raises(ValueError):
            r54.assert_p7_r54_p5_decision_candidate_separation_bodyfree_contract(mutated)


def test_r54_r19_default_blocks_until_r18_decision_is_ready() -> None:
    handoff = r54.build_p7_r54_p6_limited_human_readfeel_candidate_handoff_bodyfree()

    assert set(handoff) == set(r54.P7_R54_P6_LIMITED_HUMAN_READFEEL_CANDIDATE_HANDOFF_REQUIRED_FIELD_REFS)
    assert handoff["schema_version"] == r54.P7_R54_P6_LIMITED_HUMAN_READFEEL_CANDIDATE_HANDOFF_SCHEMA_VERSION
    assert handoff["policy_section"] == r54.P7_R54_R19_STEP_REF
    assert handoff["p6_candidate_handoff_status"] == "BLOCKED_BY_R54_18_P5_DECISION_CANDIDATE_SEPARATION"
    assert handoff["p6_limited_human_readfeel_candidate"] is False
    assert handoff["p6_limited_human_readfeel_start_allowed"] is False
    assert handoff["p6_candidate_handoff_materialized_here"] is False
    assert handoff["next_required_step"] == r54.P7_R54_R19_BLOCKED_NEXT_REQUIRED_STEP_REF

    assert r54.assert_p7_r54_p6_limited_human_readfeel_candidate_handoff_bodyfree_contract(handoff) is True
    _assert_body_free_no_runtime_promotion(handoff)


def test_r54_r19_candidate_true_only_from_p5_confirmed_but_start_allowed_false(tmp_path) -> None:
    decision = r54.build_p7_r54_p5_decision_candidate_separation_bodyfree(
        body_free_post_review_summary=_ready_summary(tmp_path),
    )
    handoff = r54.build_p7_r54_p6_limited_human_readfeel_candidate_handoff_bodyfree(
        p5_decision_candidate_separation=decision,
    )

    assert handoff["p6_candidate_handoff_status"] == "P6_CANDIDATE_TRUE_FROM_P5_CONFIRMED_CANDIDATE"
    assert handoff["p5_decision_candidate_ref"] == "P5_CONFIRMED_CANDIDATE"
    assert handoff["p5_human_blind_qa_confirmed_candidate"] is True
    assert handoff["p6_limited_human_readfeel_candidate"] is True
    assert handoff["p6_limited_human_readfeel_start_allowed"] is False
    assert "r54_p6_start_allowed_false_fixed_by_r54_scope" in handoff["p6_start_allowed_false_reason_refs"]
    assert handoff["p8_start_allowed"] is False
    assert handoff["release_allowed"] is False
    assert handoff["next_required_step"] == r54.P7_R54_R19_NEXT_REQUIRED_STEP_REF

    assert r54.assert_p7_r54_p6_limited_human_readfeel_candidate_handoff_bodyfree_contract(handoff) is True
    _assert_body_free_no_runtime_promotion(handoff)


def test_r54_r19_repair_or_inconclusive_decision_never_becomes_p6_candidate(tmp_path) -> None:
    repair_decision = r54.build_p7_r54_p5_decision_candidate_separation_bodyfree(
        body_free_post_review_summary=_repair_summary(tmp_path),
    )
    repair_handoff = r54.build_p7_r54_p6_limited_human_readfeel_candidate_handoff_bodyfree(
        p5_decision_candidate_separation=repair_decision,
    )
    assert repair_handoff["p6_candidate_handoff_status"] == "P6_CANDIDATE_NOT_AVAILABLE_P5_REPAIR_RETURN"
    assert repair_handoff["p6_limited_human_readfeel_candidate"] is False
    assert repair_handoff["p6_limited_human_readfeel_start_allowed"] is False

    inconclusive_decision = r54.build_p7_r54_p5_decision_candidate_separation_bodyfree(
        body_free_post_review_summary=_yellow_summary(tmp_path),
    )
    inconclusive_handoff = r54.build_p7_r54_p6_limited_human_readfeel_candidate_handoff_bodyfree(
        p5_decision_candidate_separation=inconclusive_decision,
    )
    assert inconclusive_handoff["p6_candidate_handoff_status"] == "P6_CANDIDATE_NOT_AVAILABLE_P5_INCONCLUSIVE"
    assert inconclusive_handoff["p6_limited_human_readfeel_candidate"] is False
    assert inconclusive_handoff["p6_limited_human_readfeel_start_allowed"] is False

    assert r54.assert_p7_r54_p6_limited_human_readfeel_candidate_handoff_bodyfree_contract(repair_handoff) is True
    assert r54.assert_p7_r54_p6_limited_human_readfeel_candidate_handoff_bodyfree_contract(inconclusive_handoff) is True
    _assert_body_free_no_runtime_promotion(repair_handoff)
    _assert_body_free_no_runtime_promotion(inconclusive_handoff)


def test_r54_r19_contract_rejects_start_allowed_or_p8_release_promotion(tmp_path) -> None:
    decision = r54.build_p7_r54_p5_decision_candidate_separation_bodyfree(
        body_free_post_review_summary=_ready_summary(tmp_path),
    )
    handoff = r54.build_p7_r54_p6_limited_human_readfeel_candidate_handoff_bodyfree(
        p5_decision_candidate_separation=decision,
    )
    for key in (
        "p6_limited_human_readfeel_start_allowed",
        "p8_start_allowed",
        "p7_complete",
        "release_allowed",
        "p5_human_blind_qa_confirmed_final",
        "actual_human_review_run_here",
        "actual_manual_review_run_here",
        "local_absolute_path_included",
        "body_content_hash_included",
    ):
        mutated = deepcopy(handoff)
        mutated[key] = True
        with pytest.raises(ValueError):
            r54.assert_p7_r54_p6_limited_human_readfeel_candidate_handoff_bodyfree_contract(mutated)
