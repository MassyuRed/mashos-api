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


def _r8_ready(tmp_path) -> dict[str, object]:
    form = r54.build_p7_r54_reviewer_instruction_rating_form_freeze_bodyfree(
        packet_completeness_export_denylist_scan=_r7_ready(tmp_path),
    )
    assert form["instruction_form_status"] == "READY_FOR_ACTUAL_HUMAN_REVIEW_OPERATION_STATE_CAPTURE"
    assert r54.assert_p7_r54_reviewer_instruction_rating_form_freeze_bodyfree_contract(form) is True
    return form


def test_r54_r8_blocks_by_default_before_r7_scan_ready() -> None:
    form = r54.build_p7_r54_reviewer_instruction_rating_form_freeze_bodyfree()

    assert set(form) == set(r54.P7_R54_REVIEWER_INSTRUCTION_RATING_FORM_FREEZE_REQUIRED_FIELD_REFS)
    assert form["schema_version"] == r54.P7_R54_REVIEWER_INSTRUCTION_RATING_FORM_FREEZE_SCHEMA_VERSION
    assert form["policy_section"] == "R54-8_reviewer_instruction_rating_form_freeze"
    assert form["instruction_form_status"] == "BLOCKED_BY_R54_7_PACKET_SCAN"
    assert form["r7_ready_for_actual_human_review"] is False
    assert form["rating_axis_refs"] == []
    assert form["rating_axis_count"] == 0
    assert form["rating_axis_instruction_rows"] == []
    assert "r54_reviewer_instruction_packet_scan_not_ready" in form["execution_blocker_ids"]
    assert form["r54_8_reviewer_instruction_rating_form_freeze_built"] is False
    assert form["question_text_field_present"] is False
    assert form["draft_question_text_field_present"] is False
    assert form["next_required_step"] == r54.P7_R54_R8_BLOCKED_NEXT_REQUIRED_STEP_REF

    assert r54.assert_p7_r54_reviewer_instruction_rating_form_freeze_bodyfree_contract(form) is True
    _assert_body_free_no_promotion(form)


def test_r54_r8_ready_freezes_reviewer_instruction_and_rating_form_without_question_text(tmp_path) -> None:
    form = _r8_ready(tmp_path)

    assert form["review_session_status"] == "R54_REVIEWER_INSTRUCTION_RATING_FORM_READY"
    assert form["r7_ready_for_actual_human_review"] is True
    assert form["required_case_count"] == 24
    assert form["packet_completion_row_count"] == 24
    assert tuple(form["rating_axis_refs"]) == r54.P5_HUMAN_BLIND_QA_RATING_AXES
    assert form["rating_axis_count"] == 6
    assert len(form["rating_axis_instruction_rows"]) == 6
    assert form["axis_score_min"] == 0.0
    assert form["axis_score_max"] == 1.0
    assert form["axis_score_bounds_enforced"] is True
    assert tuple(form["verdict_enum_refs"]) == ("PASS", "YELLOW", "REPAIR_REQUIRED", "RED")
    assert form["question_need_observation_enum_only"] is True
    assert form["question_need_observation_selection_mode"] == r54.P7_R54_QUESTION_NEED_SELECTION_MODE_REF
    assert tuple(form["question_need_primary_class_refs"]) == r54.P7_R49_QUESTION_NEED_PRIMARY_CLASS_REFS
    assert tuple(form["ambiguity_kind_refs"]) == r54.P7_R49_AMBIGUITY_KIND_REFS
    assert tuple(form["one_question_fit_refs"]) == r54.P7_R49_ONE_QUESTION_FIT_REFS
    assert tuple(form["repair_required_ref_refs"]) == r54.P7_R49_REPAIR_REQUIRED_REF_REFS
    assert form["question_text_field_present"] is False
    assert form["draft_question_text_field_present"] is False
    assert form["question_text_entry_allowed"] is False
    assert form["reviewer_free_text_allowed"] is False
    assert form["reviewer_notes_local_only_if_any"] is True
    assert form["reviewer_notes_purge_required"] is True
    assert form["reviewer_notes_body_stored_here"] is False
    assert form["machine_auto_score_used"] is False
    assert form["machine_metrics_used_for_readfeel"] is False
    assert form["reviewer_selections_required_for_rating"] is True
    assert form["not_reviewed_rating_rows_allowed"] is False
    assert form["actual_human_review_run_here"] is False
    assert form["actual_rating_rows_materialized_here"] is False
    assert form["actual_question_need_observation_rows_materialized_here"] is False
    assert form["execution_blocker_ids"] == []
    assert tuple(form["implemented_steps"]) == r54.P7_R54_R8_IMPLEMENTED_STEPS
    assert tuple(form["not_yet_implemented_steps"]) == r54.P7_R54_R8_NOT_YET_IMPLEMENTED_STEPS
    assert form["next_required_step"] == r54.P7_R54_R8_NEXT_REQUIRED_STEP_REF

    first_axis = form["rating_axis_instruction_rows"][0]
    assert set(first_axis) == set(r54.P7_R54_REVIEWER_RATING_AXIS_INSTRUCTION_ROW_REQUIRED_FIELD_REFS)
    assert first_axis["score_min"] == 0.0
    assert first_axis["score_max"] == 1.0
    assert first_axis["score_value_source_ref"] == "reviewer_selection_only"
    assert first_axis["machine_auto_score_allowed"] is False
    assert first_axis["reviewer_selection_required"] is True

    _assert_body_free_no_promotion(form)


@pytest.mark.parametrize(
    "key,value",
    [
        ("question_text_field_present", True),
        ("draft_question_text_field_present", True),
        ("question_text_entry_allowed", True),
        ("reviewer_free_text_allowed", True),
        ("reviewer_notes_body_stored_here", True),
        ("machine_auto_score_used", True),
        ("machine_metrics_used_for_readfeel", True),
        ("not_reviewed_rating_rows_allowed", True),
        ("actual_human_review_run_here", True),
        ("actual_rating_rows_materialized_here", True),
        ("actual_question_need_observation_rows_materialized_here", True),
        ("body_full_packet_generated_here", True),
        ("p8_start_allowed", True),
        ("release_allowed", True),
    ],
)
def test_r54_r8_rejects_question_text_free_text_machine_rating_or_promotion_mutation(tmp_path, key: str, value: object) -> None:
    form = _r8_ready(tmp_path)
    form[key] = value
    with pytest.raises(ValueError):
        r54.assert_p7_r54_reviewer_instruction_rating_form_freeze_bodyfree_contract(form)


def test_r54_r8_rejects_axis_row_score_bound_mutation(tmp_path) -> None:
    form = _r8_ready(tmp_path)
    form["rating_axis_instruction_rows"][0] = deepcopy(form["rating_axis_instruction_rows"][0])
    form["rating_axis_instruction_rows"][0]["score_max"] = 5.0
    with pytest.raises(ValueError):
        r54.assert_p7_r54_reviewer_instruction_rating_form_freeze_bodyfree_contract(form)


def test_r54_r9_blocks_by_default_before_r8_form_ready() -> None:
    state = r54.build_p7_r54_actual_human_review_operation_state_capture_bodyfree()

    assert set(state) == set(r54.P7_R54_ACTUAL_HUMAN_REVIEW_OPERATION_STATE_CAPTURE_REQUIRED_FIELD_REFS)
    assert state["schema_version"] == r54.P7_R54_ACTUAL_HUMAN_REVIEW_OPERATION_STATE_CAPTURE_SCHEMA_VERSION
    assert state["policy_section"] == "R54-9_actual_human_review_operation_state_capture"
    assert state["operation_state_capture_status"] == "BLOCKED_BY_R54_8_FORM"
    assert state["r8_instruction_form_ready_for_operation_state_capture"] is False
    assert "r54_actual_review_operation_form_not_ready" in state["execution_blocker_ids"]
    assert state["actual_review_operation_state_captured_here"] is False
    assert state["ready_for_sanitized_actual_review_result_capture"] is False
    assert state["actual_human_review_run_here"] is False
    assert state["actual_rating_rows_materialized_here"] is False
    assert state["next_required_step"] == r54.P7_R54_R9_BLOCKED_NEXT_STEP_REF

    assert r54.assert_p7_r54_actual_human_review_operation_state_capture_bodyfree_contract(state) is True
    _assert_body_free_no_promotion(state)


def test_r54_r9_not_started_captures_operation_state_without_rating_rows(tmp_path) -> None:
    state = r54.build_p7_r54_actual_human_review_operation_state_capture_bodyfree(
        reviewer_instruction_rating_form_freeze=_r8_ready(tmp_path),
        review_operation_state_ref="not_started",
    )

    assert state["review_operation_state_ref"] == "not_started"
    assert state["review_session_status"] == "R54_READY_FOR_ACTUAL_HUMAN_REVIEW_NOT_STARTED"
    assert state["operation_state_capture_status"] == "R54_REVIEW_OPERATION_STATE_CAPTURED_PENDING"
    assert state["operation_pending_without_rating_rows"] is True
    assert state["reviewer_selection_count"] == 0
    assert state["ready_for_sanitized_actual_review_result_capture"] is False
    assert state["handoff_to_r54_10_allowed"] is False
    assert state["machine_auto_score_used"] is False
    assert state["machine_metrics_used_for_readfeel"] is False
    assert state["reviewer_selections_only_rating_source"] is True
    assert state["not_reviewed_rating_rows_allowed"] is False
    assert state["rating_rows_created_for_not_reviewed"] is False
    assert state["actual_human_review_run_here"] is False
    assert state["actual_rating_rows_materialized_here"] is False
    assert state["actual_question_need_observation_rows_materialized_here"] is False
    assert state["execution_blocker_ids"] == []
    assert tuple(state["implemented_steps"]) == r54.P7_R54_R9_IMPLEMENTED_STEPS
    assert state["next_required_step"] == r54.P7_R54_R9_OPERATION_PENDING_NEXT_STEP_REF

    _assert_body_free_no_promotion(state)


def test_r54_r9_capture_ready_uses_external_reviewer_selection_count_only_without_rating_rows(tmp_path) -> None:
    state = r54.build_p7_r54_actual_human_review_operation_state_capture_bodyfree(
        reviewer_instruction_rating_form_freeze=_r8_ready(tmp_path),
        review_operation_state_ref="review_completed_pending_sanitized_capture",
        reviewer_selection_count=24,
        reviewer_selection_source_ref="external_local_only_review_form_selection_count_only",
    )

    assert state["review_session_status"] == "R54_REVIEW_COMPLETED_PENDING_SANITIZED_CAPTURE"
    assert state["operation_state_capture_status"] == "READY_FOR_SANITIZED_ACTUAL_REVIEW_RESULT_CAPTURE"
    assert state["reviewer_selection_count"] == 24
    assert state["reviewer_selection_count_matches_required_case_count"] is True
    assert state["reviewer_selection_rows_materialized_here"] is False
    assert state["reviewer_selection_body_stored_here"] is False
    assert state["ready_for_sanitized_actual_review_result_capture"] is True
    assert state["capture_ready_requires_reviewer_selections"] is True
    assert state["handoff_to_r54_10_allowed"] is True
    assert state["actual_review_completed_claimed_here"] is False
    assert state["actual_human_review_run_here"] is False
    assert state["actual_rating_rows_materialized_here"] is False
    assert state["actual_question_need_observation_rows_materialized_here"] is False
    assert state["machine_auto_score_used"] is False
    assert state["machine_metrics_used_for_readfeel"] is False
    assert state["execution_blocker_ids"] == []
    assert tuple(state["implemented_steps"]) == r54.P7_R54_R9_IMPLEMENTED_STEPS
    assert tuple(state["not_yet_implemented_steps"]) == r54.P7_R54_R9_NOT_YET_IMPLEMENTED_STEPS
    assert state["next_required_step"] == r54.P7_R54_R9_NEXT_REQUIRED_STEP_REF

    _assert_body_free_no_promotion(state)


def test_r54_r9_not_reviewed_with_selection_count_blocks_rating_rows(tmp_path) -> None:
    state = r54.build_p7_r54_actual_human_review_operation_state_capture_bodyfree(
        reviewer_instruction_rating_form_freeze=_r8_ready(tmp_path),
        review_operation_state_ref="not_started",
        reviewer_selection_count=1,
    )

    assert "r54_actual_review_operation_not_reviewed_has_selection_count" in state["execution_blocker_ids"]
    assert state["ready_for_sanitized_actual_review_result_capture"] is False
    assert state["rating_rows_created_for_not_reviewed"] is False
    assert state["actual_rating_rows_materialized_here"] is False
    assert state["next_required_step"] == r54.P7_R54_R9_BLOCKED_NEXT_STEP_REF

    assert r54.assert_p7_r54_actual_human_review_operation_state_capture_bodyfree_contract(state) is True
    _assert_body_free_no_promotion(state)


def test_r54_r9_abort_or_expiration_routes_to_purge_before_handoff(tmp_path) -> None:
    state = r54.build_p7_r54_actual_human_review_operation_state_capture_bodyfree(
        reviewer_instruction_rating_form_freeze=_r8_ready(tmp_path),
        review_operation_state_ref="aborted_purge_required",
    )

    assert state["review_session_status"] == "R54_ABORTED_PURGE_REQUIRED"
    assert state["operation_state_capture_status"] == "PURGE_REQUIRED_BEFORE_HANDOFF"
    assert state["purge_required_before_handoff"] is True
    assert state["ready_for_sanitized_actual_review_result_capture"] is False
    assert state["handoff_to_r54_10_allowed"] is False
    assert state["actual_human_review_run_here"] is False
    assert state["next_required_step"] == r54.P7_R54_R9_PURGE_REQUIRED_NEXT_STEP_REF

    assert r54.assert_p7_r54_actual_human_review_operation_state_capture_bodyfree_contract(state) is True
    _assert_body_free_no_promotion(state)


@pytest.mark.parametrize(
    "key,value",
    [
        ("machine_auto_score_used", True),
        ("machine_metrics_used_for_readfeel", True),
        ("machine_generated_rating_rows_allowed", True),
        ("not_reviewed_rating_rows_allowed", True),
        ("rating_rows_created_for_not_reviewed", True),
        ("reviewer_selection_rows_materialized_here", True),
        ("reviewer_selection_body_stored_here", True),
        ("reviewer_free_text_body_stored_here", True),
        ("actual_review_completed_claimed_here", True),
        ("actual_human_review_run_here", True),
        ("actual_rating_rows_materialized_here", True),
        ("actual_question_need_observation_rows_materialized_here", True),
        ("raw_input_included", True),
        ("question_text_included", True),
        ("p6_limited_human_readfeel_start_allowed", True),
        ("p8_start_allowed", True),
        ("release_allowed", True),
    ],
)
def test_r54_r9_rejects_machine_rating_rows_body_leak_or_promotion_mutation(tmp_path, key: str, value: object) -> None:
    state = r54.build_p7_r54_actual_human_review_operation_state_capture_bodyfree(
        reviewer_instruction_rating_form_freeze=_r8_ready(tmp_path),
        review_operation_state_ref="review_completed_pending_sanitized_capture",
        reviewer_selection_count=24,
    )
    state[key] = value
    with pytest.raises(ValueError):
        r54.assert_p7_r54_actual_human_review_operation_state_capture_bodyfree_contract(state)
