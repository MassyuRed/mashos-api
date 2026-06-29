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
FORBIDDEN_PROMOTION_TRUE_TOKENS = (
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
    '"actual_disposal_receipt_materialized_here": true',
    '"disposal_receipt_materialized_here": true',
    '"p5_human_blind_qa_confirmed_candidate": true',
)


def _assert_body_free_no_runtime_promotion(material: dict[str, object]) -> None:
    dumped = json.dumps(material, ensure_ascii=False, sort_keys=True).lower()
    for forbidden in FORBIDDEN_BODY_TOKENS:
        assert forbidden not in dumped
    for forbidden in FORBIDDEN_PROMOTION_TRUE_TOKENS:
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


def _r14_ready(tmp_path) -> dict[str, object]:
    capture = _r10_ready(tmp_path)
    rating = _r11_ready(tmp_path, capture=capture)
    question = _r13_ready(tmp_path, capture=capture, rating=rating)
    guard = r54.build_p7_r54_rating_question_observation_consistency_guard_bodyfree(
        question_need_observation_row_normalization=question,
        rating_row_normalization=rating,
    )
    assert guard["rating_question_consistency_guard_status"] == "READY_FOR_PAUSE_ABORT_EXPIRATION_PROTOCOL"
    return guard


def _manifest_and_review_rows(tmp_path) -> tuple[dict[str, object], list[dict[str, object]]]:
    manifest = _r5_ready(tmp_path)
    return manifest, _review_rows_from_manifest(manifest)


def test_r54_r14_default_blocks_without_r13_and_r11() -> None:
    guard = r54.build_p7_r54_rating_question_observation_consistency_guard_bodyfree()

    assert set(guard) == set(r54.P7_R54_RATING_QUESTION_OBSERVATION_CONSISTENCY_GUARD_REQUIRED_FIELD_REFS)
    assert guard["schema_version"] == r54.P7_R54_RATING_QUESTION_OBSERVATION_CONSISTENCY_GUARD_SCHEMA_VERSION
    assert guard["policy_section"] == r54.P7_R54_R14_STEP_REF
    assert guard["rating_question_consistency_guard_status"] == "BLOCKED_BY_R54_13_OR_R54_11_PRECHECK"
    assert guard["r13_ready_for_rating_question_consistency_guard"] is False
    assert guard["r11_ready_for_rating_question_consistency_guard"] is False
    assert guard["consistency_issue_count"] == 0
    assert guard["p5_decision_candidate_not_materialized_here"] is True
    assert guard["ready_for_pause_abort_expiration_protocol"] is False
    assert guard["r54_14_rating_question_observation_consistency_guard_built"] is False
    assert guard["next_required_step"] == r54.P7_R54_R14_PRECHECK_BLOCKED_NEXT_REQUIRED_STEP_REF

    assert r54.assert_p7_r54_rating_question_observation_consistency_guard_bodyfree_contract(guard) is True
    _assert_body_free_no_runtime_promotion(guard)


def test_r54_r14_ready_passes_zero_issues_without_p5_p6_p8_promotion(tmp_path) -> None:
    guard = _r14_ready(tmp_path)

    assert guard["review_session_status"] == "R54_RATING_QUESTION_OBSERVATION_CONSISTENCY_GUARD_READY"
    assert guard["rating_row_count"] == 24
    assert guard["question_observation_row_count"] == 24
    assert guard["rating_question_case_ref_sets_match"] is True
    assert guard["all_required_rating_and_question_rows_present"] is True
    assert guard["rating_question_consistency_issue_rows"] == []
    assert guard["consistency_issue_count"] == 0
    assert guard["p5_confirmed_candidate_blocked_by_consistency_issues"] is False
    assert guard["p5_decision_candidate_not_materialized_here"] is True
    assert guard["p8_material_candidates_do_not_hide_p5_repair_here"] is True
    assert guard["ready_for_pause_abort_expiration_protocol"] is True
    assert guard["actual_rating_rows_materialized_here"] is True
    assert guard["actual_question_need_observation_rows_materialized_here"] is True
    assert guard["actual_human_review_run_here"] is False
    assert guard["p8_start_allowed"] is False
    assert guard["p6_limited_human_readfeel_start_allowed"] is False
    assert tuple(guard["implemented_steps"]) == r54.P7_R54_R14_IMPLEMENTED_STEPS
    assert tuple(guard["not_yet_implemented_steps"]) == r54.P7_R54_R14_NOT_YET_IMPLEMENTED_STEPS
    assert guard["next_required_step"] == r54.P7_R54_R14_NEXT_REQUIRED_STEP_REF

    assert r54.assert_p7_r54_rating_question_observation_consistency_guard_bodyfree_contract(guard) is True
    _assert_body_free_no_runtime_promotion(guard)


def test_r54_r14_detects_rating_question_semantic_contradictions(tmp_path) -> None:
    manifest, rows = _manifest_and_review_rows(tmp_path)
    first, second, third, fourth = manifest["controller_manifest_rows"][:4]
    rows[0] = r54.build_p7_r54_sanitized_review_result_row_bodyfree(
        blind_case_id=first["blind_case_id"],
        case_ref_id=first["case_ref_id"],
        packet_ref_id=first["packet_ref_id"],
        case_family_ref=first["family"],
        case_role_ref=first["case_role"],
        subscription_boundary_ref=_subscription_boundary(first),
        verdict="RED",
        readfeel_blocker_ids=("p5_history_connection_too_generic",),
        question_need_primary_class="no_question_needed_emlis_can_observe",
    )
    rows[1] = r54.build_p7_r54_sanitized_review_result_row_bodyfree(
        blind_case_id=second["blind_case_id"],
        case_ref_id=second["case_ref_id"],
        packet_ref_id=second["packet_ref_id"],
        case_family_ref=second["family"],
        case_role_ref=second["case_role"],
        subscription_boundary_ref=_subscription_boundary(second),
        verdict="REPAIR_REQUIRED",
        readfeel_blocker_ids=("p5_history_connection_too_generic",),
        question_need_primary_class="plus_single_question_candidate_later",
        one_question_fit_ref="fits_one_question",
    )
    rows[2] = r54.build_p7_r54_sanitized_review_result_row_bodyfree(
        blind_case_id=third["blind_case_id"],
        case_ref_id=third["case_ref_id"],
        packet_ref_id=third["packet_ref_id"],
        case_family_ref=third["family"],
        case_role_ref=third["case_role"],
        subscription_boundary_ref=_subscription_boundary(third),
        verdict="PASS",
        question_need_primary_class="not_question_p5_surface_repair_required",
        one_question_fit_ref="repair_required_not_question",
        repair_required_refs=("p5_surface_repair_required",),
    )
    rows[3] = r54.build_p7_r54_sanitized_review_result_row_bodyfree(
        blind_case_id=fourth["blind_case_id"],
        case_ref_id=fourth["case_ref_id"],
        packet_ref_id=fourth["packet_ref_id"],
        case_family_ref=fourth["family"],
        case_role_ref=fourth["case_role"],
        subscription_boundary_ref=_subscription_boundary(fourth),
        verdict="PASS",
        question_need_primary_class="insufficient_material_execution_blocker",
        one_question_fit_ref="insufficient_material",
    )
    capture = _r10_ready(tmp_path, rows=rows)
    rating = _r11_ready(tmp_path, capture=capture)
    question = _r13_ready(tmp_path, capture=capture, rating=rating)
    guard = r54.build_p7_r54_rating_question_observation_consistency_guard_bodyfree(
        question_need_observation_row_normalization=question,
        rating_row_normalization=rating,
    )

    assert guard["rating_question_consistency_guard_status"] == "BLOCKED_BY_RATING_QUESTION_OBSERVATION_CONSISTENCY_ISSUES"
    assert guard["consistency_issue_count"] == 4
    assert guard["red_with_no_question_needed_observation_count"] == 1
    assert guard["repair_required_with_p8_question_candidate_count"] == 1
    assert guard["pass_with_not_question_repair_required_count"] == 1
    assert guard["insufficient_material_with_pass_or_no_execution_blocker_count"] == 1
    assert guard["p5_confirmed_candidate_blocked_by_consistency_issues"] is True
    assert guard["issues_route_to_p5_repair_return_or_inconclusive_later"] is True
    assert guard["ready_for_pause_abort_expiration_protocol"] is False
    assert guard["p8_material_candidates_do_not_hide_p5_repair_here"] is True
    assert guard["p8_start_allowed"] is False
    assert guard["next_required_step"] == r54.P7_R54_R14_BLOCKED_NEXT_REQUIRED_STEP_REF

    issue_ids = {row["issue_id"] for row in guard["rating_question_consistency_issue_rows"]}
    assert {
        "r54_red_with_no_question_needed_observation",
        "r54_repair_required_with_p8_question_candidate",
        "r54_pass_with_not_question_repair_required",
        "r54_insufficient_material_with_pass_or_no_execution_blocker",
    } <= issue_ids
    assert r54.assert_p7_r54_rating_question_observation_consistency_guard_bodyfree_contract(guard) is True
    _assert_body_free_no_runtime_promotion(guard)


def test_r54_r14_contract_rejects_ready_material_with_issue_count(tmp_path) -> None:
    guard = _r14_ready(tmp_path)
    mutated = deepcopy(guard)
    mutated["consistency_issue_count"] = 1
    mutated["rating_question_consistency_issue_rows"] = [
        r54.build_p7_r54_rating_question_consistency_issue_row_bodyfree(
            issue_id="r54_red_with_no_question_needed_observation",
            issue_kind_ref="p5_repair_return_consistency_issue",
            decision_direction_ref="p5_repair_return_required_later",
        )
    ]
    with pytest.raises(ValueError):
        r54.assert_p7_r54_rating_question_observation_consistency_guard_bodyfree_contract(mutated)


def test_r54_r14_contract_rejects_p5_or_p8_promotion(tmp_path) -> None:
    guard = _r14_ready(tmp_path)
    for key in ("p5_human_blind_qa_confirmed_candidate", "p8_start_allowed", "p6_limited_human_readfeel_start_allowed", "release_allowed"):
        mutated = deepcopy(guard)
        mutated[key] = True
        with pytest.raises(ValueError):
            r54.assert_p7_r54_rating_question_observation_consistency_guard_bodyfree_contract(mutated)


def test_r54_r15_default_continue_blocks_until_r14_ready() -> None:
    protocol = r54.build_p7_r54_pause_abort_expiration_protocol_bodyfree()

    assert set(protocol) == set(r54.P7_R54_PAUSE_ABORT_EXPIRATION_PROTOCOL_REQUIRED_FIELD_REFS)
    assert protocol["schema_version"] == r54.P7_R54_PAUSE_ABORT_EXPIRATION_PROTOCOL_SCHEMA_VERSION
    assert protocol["policy_section"] == r54.P7_R54_R15_STEP_REF
    assert protocol["pause_abort_expiration_protocol_status"] == "BLOCKED_BY_R54_14_CONSISTENCY_GUARD"
    assert protocol["r14_ready_for_pause_abort_expiration_protocol"] is False
    assert protocol["purge_required_before_any_handoff"] is False
    assert protocol["purge_before_handoff_required"] is True
    assert protocol["handoff_allowed_before_purge"] is False
    assert protocol["r52_reintake_handoff_allowed_before_purge"] is False
    assert protocol["p5_decision_materialized_here"] is False
    assert protocol["r54_15_pause_abort_expiration_protocol_built"] is False
    assert protocol["next_required_step"] == r54.P7_R54_R15_BLOCKED_NEXT_REQUIRED_STEP_REF

    assert r54.assert_p7_r54_pause_abort_expiration_protocol_bodyfree_contract(protocol) is True
    _assert_body_free_no_runtime_promotion(protocol)


def test_r54_r15_continue_after_ready_guard_requires_purge_before_any_handoff(tmp_path) -> None:
    protocol = r54.build_p7_r54_pause_abort_expiration_protocol_bodyfree(
        rating_question_observation_consistency_guard=_r14_ready(tmp_path),
    )

    assert protocol["pause_abort_expiration_protocol_status"] == "READY_FOR_PURGE_DISPOSAL_RECEIPT"
    assert protocol["protocol_action_ref"] == "continue_after_consistency_guard"
    assert protocol["r14_ready_for_pause_abort_expiration_protocol"] is True
    assert protocol["review_can_continue_to_purge_disposal_receipt"] is True
    assert protocol["purge_required_before_any_handoff"] is True
    assert protocol["purge_before_handoff_required"] is True
    assert protocol["handoff_allowed_before_purge"] is False
    assert protocol["r52_reintake_handoff_allowed_before_purge"] is False
    assert protocol["disposal_receipt_materialized_here"] is False
    assert protocol["actual_disposal_receipt_materialized_here"] is False
    assert protocol["p5_decision_direction_ref"] == "no_p5_decision_materialized_here"
    assert protocol["p5_decision_materialized_here"] is False
    assert protocol["r54_15_pause_abort_expiration_protocol_built"] is True
    assert tuple(protocol["implemented_steps"]) == r54.P7_R54_R15_IMPLEMENTED_STEPS
    assert tuple(protocol["not_yet_implemented_steps"]) == r54.P7_R54_R15_NOT_YET_IMPLEMENTED_STEPS
    assert protocol["next_required_step"] == r54.P7_R54_R15_NEXT_REQUIRED_STEP_REF

    assert r54.assert_p7_r54_pause_abort_expiration_protocol_bodyfree_contract(protocol) is True
    _assert_body_free_no_runtime_promotion(protocol)


@pytest.mark.parametrize(
    ("action", "status", "direction"),
    [
        ("aborted_purge_required", "ABORTED_PURGE_REQUIRED", "p5_inconclusive_due_to_abort_or_expiration"),
        ("expired_purge_required", "EXPIRED_PURGE_REQUIRED", "p5_inconclusive_due_to_abort_or_expiration"),
        ("rating_incomplete_purge_required", "RATING_INCOMPLETE_PURGE_REQUIRED", "p5_inconclusive_due_to_rating_incomplete"),
    ],
)
def test_r54_r15_abort_expired_or_rating_incomplete_routes_to_purge_and_inconclusive_direction_only(tmp_path, action: str, status: str, direction: str) -> None:
    protocol = r54.build_p7_r54_pause_abort_expiration_protocol_bodyfree(
        rating_question_observation_consistency_guard=_r14_ready(tmp_path),
        protocol_action_ref=action,
    )

    assert protocol["pause_abort_expiration_protocol_status"] == status
    assert protocol["protocol_action_ref"] == action
    assert protocol["purge_required_before_any_handoff"] is True
    assert protocol["handoff_allowed_before_purge"] is False
    assert protocol["r52_reintake_handoff_allowed_before_purge"] is False
    assert protocol["p5_decision_direction_ref"] == direction
    assert protocol["p5_inconclusive_direction_only_not_decision_materialized"] is True
    assert protocol["p5_decision_materialized_here"] is False
    assert protocol["disposal_receipt_materialized_here"] is False
    assert protocol["actual_disposal_receipt_materialized_here"] is False
    assert protocol["next_required_step"] == r54.P7_R54_R15_NEXT_REQUIRED_STEP_REF

    assert r54.assert_p7_r54_pause_abort_expiration_protocol_bodyfree_contract(protocol) is True
    _assert_body_free_no_runtime_promotion(protocol)


def test_r54_r15_pause_state_never_handoffs_before_return_or_purge(tmp_path) -> None:
    protocol = r54.build_p7_r54_pause_abort_expiration_protocol_bodyfree(
        rating_question_observation_consistency_guard=_r14_ready(tmp_path),
        protocol_action_ref="paused_pending_reviewer_return",
    )

    assert protocol["pause_abort_expiration_protocol_status"] == "PAUSED_NO_HANDOFF_LOCAL_ONLY"
    assert protocol["review_paused_without_handoff"] is True
    assert protocol["purge_required_before_any_handoff"] is False
    assert protocol["purge_before_handoff_required"] is True
    assert protocol["handoff_allowed_before_purge"] is False
    assert protocol["r52_reintake_handoff_allowed_before_purge"] is False
    assert protocol["p5_decision_direction_ref"] == "p5_inconclusive_due_to_pause_without_handoff"
    assert protocol["p5_decision_materialized_here"] is False
    assert protocol["next_required_step"] == r54.P7_R54_R15_PAUSED_NEXT_REQUIRED_STEP_REF

    assert r54.assert_p7_r54_pause_abort_expiration_protocol_bodyfree_contract(protocol) is True
    _assert_body_free_no_runtime_promotion(protocol)


def test_r54_r15_rejects_unknown_protocol_action(tmp_path) -> None:
    with pytest.raises(ValueError):
        r54.build_p7_r54_pause_abort_expiration_protocol_bodyfree(
            rating_question_observation_consistency_guard=_r14_ready(tmp_path),
            protocol_action_ref="unsafe_handoff_before_purge",
        )


@pytest.mark.parametrize(
    "key",
    [
        "handoff_allowed_before_purge",
        "r52_reintake_handoff_allowed_before_purge",
        "p5_decision_materialized_here",
        "disposal_receipt_materialized_here",
        "actual_disposal_receipt_materialized_here",
        "post_review_summary_materialized_here",
        "actual_human_review_run_here",
        "actual_manual_review_run_here",
        "p6_limited_human_readfeel_start_allowed",
        "p8_start_allowed",
        "release_allowed",
        "api_db_rn_response_key_changed_here",
        "runtime_changed_here",
    ],
)
def test_r54_r15_contract_rejects_handoff_disposal_decision_review_or_runtime_promotion(tmp_path, key: str) -> None:
    protocol = r54.build_p7_r54_pause_abort_expiration_protocol_bodyfree(
        rating_question_observation_consistency_guard=_r14_ready(tmp_path),
    )
    mutated = deepcopy(protocol)
    mutated[key] = True
    with pytest.raises(ValueError):
        r54.assert_p7_r54_pause_abort_expiration_protocol_bodyfree_contract(mutated)
