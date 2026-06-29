# -*- coding: utf-8 -*-
"""R50-6/R50-7 tests for P5 human Blind QA manual-run decision.

These tests intentionally stop at the local-only body-full packet generation
request and reviewer instruction/rating form freeze.  They do not write
body-full packets, run actual human review, materialize rating rows, materialize
question observation rows, touch API/DB/RN contracts, start P8, complete P7, or
claim release readiness.
"""

from __future__ import annotations

import copy

import pytest

import emlis_ai_p7_r50_p5_human_blind_qa_manual_run_decision as r50


_VALID_LOCAL_ROOT_REF = "/tmp/cocolon_emlis_r50_local_review"
_SAFE_BODYFREE_EXPORT_CANDIDATE_REF = "summary.bodyfree/post_review_decision_summary.bodyfree.json"

_FALSE_RUNTIME_AND_PRODUCT_FLAGS = (
    "actual_human_review_run_here",
    "actual_manual_review_run_here",
    "body_full_packet_generated_here",
    "body_full_packets_created_local_only",
    "api_db_rn_response_key_changed_here",
    "question_api_implemented",
    "question_db_schema_implemented",
    "question_rn_ui_implemented",
    "question_response_key_implemented",
    "question_trigger_logic_implemented",
    "p5_human_blind_qa_confirmed",
    "p5_human_blind_qa_confirmed_candidate",
    "p6_limited_human_readfeel_start_allowed",
    "p6_limited_human_readfeel_start_allowed_candidate",
    "p8_question_design_material_candidate",
    "p7_complete",
    "p8_start_allowed",
    "release_allowed",
)

_BODY_LEAK_FIELD_REFS = (
    "raw_input",
    "raw_answer",
    "comment_text",
    "comment_text_body",
    "returned_emlis_surface",
    "bounded_owned_history_review_surface",
    "current_input_review_surface",
    "reviewer_free_text",
    "reviewer_note",
    "reviewer_notes",
    "question_text",
    "draft_question_text",
    "question_body",
    "local_absolute_path",
    "body_content_hash",
    "packet_content_hash",
    "terminal_output",
    "stdout",
    "stderr",
    "traceback",
)


def _walk_keys(value):
    if isinstance(value, dict):
        for key, child in value.items():
            yield str(key)
            yield from _walk_keys(child)
    elif isinstance(value, (list, tuple)):
        for child in value:
            yield from _walk_keys(child)


def _assert_body_free_no_leak(value):
    keys = set(_walk_keys(value))
    assert not (keys & set(_BODY_LEAK_FIELD_REFS))


def _r3_go():
    return r50.build_p7_r50_manual_run_decision_bodyfree(
        local_review_root_safe=True,
        explicit_allow_present=True,
        disposal_plan_ready=True,
        body_free_summary_path_ready=True,
    )


def _r4_passed():
    return r50.build_p7_r50_local_only_root_explicit_allow_export_denylist_preflight(
        manual_run_decision_bodyfree=_r3_go(),
        local_review_root=_VALID_LOCAL_ROOT_REF,
        explicit_allow_token=r50.P7_R50_EXPLICIT_BODY_FULL_ALLOW_TOKEN_REF,
        export_candidate_refs=[_SAFE_BODYFREE_EXPORT_CANDIDATE_REF],
    )


def _r5_ready():
    return r50.build_p7_r50_review_session_protocol_bodyfree(
        local_only_root_explicit_allow_export_preflight=_r4_passed()
    )


def _r6_ready():
    return r50.build_p7_r50_local_only_body_full_packet_generation_request(
        review_session_protocol_bodyfree=_r5_ready()
    )


def _assert_no_runtime_or_product_completion(material):
    for key in _FALSE_RUNTIME_AND_PRODUCT_FLAGS:
        assert material[key] is False
    assert material["body_free"] is True
    _assert_body_free_no_leak(material)


def test_r50_received_source_contains_r0_to_r5_before_r6_r7_progression():
    assert r50.P7_R50_R5_IMPLEMENTED_STEPS == (
        "R50-0_current_source_r49_handoff_p7_p8_bridge_refreeze",
        "R50-1_scope_schema_version_status_enum_freeze",
        "R50-2_prior_validation_evidence_adoption",
        "R50-3_manual_run_go_no_go_decision_builder",
        "R50-4_local_only_root_explicit_allow_export_denylist_preflight",
        "R50-5_24_case_review_session_protocol_builder",
    )
    assert r50.P7_R50_R5_NOT_YET_IMPLEMENTED_STEPS[0] == "R50-6_local_only_body_full_packet_generation_request"
    assert r50.P7_R50_R5_NEXT_REQUIRED_STEP_REF == "R50-6_local_only_body_full_packet_generation_request"


def test_r50_r6_builds_local_only_body_full_packet_generation_request_without_writing_packets():
    request = _r6_ready()

    assert r50.assert_p7_r50_local_only_body_full_packet_generation_request_contract(request) is True
    assert request["schema_version"] == r50.P7_R50_LOCAL_ONLY_BODY_FULL_PACKET_GENERATION_REQUEST_SCHEMA_VERSION
    assert request["policy_section"] == "R50-6_local_only_body_full_packet_generation_request"
    assert request["protocol_status"] == "READY_FOR_24_CASE_LOCAL_REVIEW_PROTOCOL"
    assert request["request_status"] == "READY_FOR_LOCAL_ONLY_BODY_FULL_PACKET_GENERATION_REQUEST"
    assert request["review_session_status"] == "READY_FOR_LOCAL_BODY_FULL_PACKET_GENERATION"
    assert request["local_only_request"] is True
    assert request["local_review_root_ref"] == "COCOLON_EMLIS_LOCAL_REVIEW_ROOT"
    assert request["explicit_allow_token_ref"] == "LOCAL_ONLY_REVIEW_CONFIRMED"
    assert request["storage_root_ref"] == "external_local_review_root"
    assert request["root_path_exposed"] is False
    assert request["local_absolute_path_included"] is False
    assert request["required_case_count"] == 24
    assert request["case_distribution_total"] == 24
    assert request["packet_ref_manifest_expected_count"] == 24
    assert request["body_full_packet_retention_max_hours"] == r50.P7_R47_BODY_FULL_PACKET_RETENTION_HOURS == 72
    assert request["reviewer_notes_retention_after_rating_hours"] == (
        r50.P7_R47_REVIEWER_NOTES_RETENTION_AFTER_RATING_HOURS
    ) == 24
    assert request["reviewer_notes_retention_after_rating_hours"] != 0
    assert request["disposal_required"] is True
    assert request["disposal_receipt_required"] is True
    assert request["body_free_export_allowed_before_disposal"] is False
    assert request["release_material_inclusion_allowed"] is False
    assert request["artifact_zip_inclusion_allowed"] is False
    assert request["premise_or_implemented_docs_inclusion_allowed"] is False
    assert request["local_packet_exported"] is False
    assert request["content_hash_of_body_stored"] is False
    assert request["reviewer_packet_body_source_refs_stored_here"] is False
    assert request["local_path_stored_here"] is False
    assert request["body_content_hash_stored_here"] is False
    assert request["command_executed_here"] is False
    assert request["file_written_here"] is False
    assert request["body_full_packet_generation_request_created_here"] is True
    assert request["body_full_packet_generation_allowed_for_next_manual_step"] is True
    assert request["body_full_packet_generation_executed_here"] is False
    assert request["body_full_packet_generated_here"] is False
    assert request["body_full_packets_created_local_only"] is False
    assert request["body_full_writer_created_here"] is False
    assert request["local_reviewer_payload_materialized_here"] is False
    assert request["implemented_steps"] == list(r50.P7_R50_R6_IMPLEMENTED_STEPS)
    assert request["not_yet_implemented_steps"] == list(r50.P7_R50_R6_NOT_YET_IMPLEMENTED_STEPS)
    assert request["next_required_step"] == r50.P7_R50_R6_NEXT_REQUIRED_STEP_REF
    _assert_no_runtime_or_product_completion(request)


def test_r50_r6_blocks_packet_generation_request_when_r5_protocol_is_blocked():
    blocked_r4 = r50.build_p7_r50_local_only_root_explicit_allow_export_denylist_preflight(
        manual_run_decision_bodyfree=_r3_go(),
        local_review_root=_VALID_LOCAL_ROOT_REF,
        explicit_allow_token="WRONG_TOKEN",
    )
    blocked_r5 = r50.build_p7_r50_review_session_protocol_bodyfree(
        local_only_root_explicit_allow_export_preflight=blocked_r4
    )
    request = r50.build_p7_r50_local_only_body_full_packet_generation_request(
        review_session_protocol_bodyfree=blocked_r5
    )

    assert request["protocol_status"] == "BLOCKED_BY_R50_4_PREFLIGHT"
    assert request["request_status"] == "BLOCKED_BY_R50_5_PROTOCOL"
    assert request["local_only_body_full_generation_allowed"] is False
    assert request["body_full_packet_generation_allowed_for_next_manual_step"] is False
    assert request["packet_ref_manifest_expected_count"] == 0
    assert "r50_explicit_allow_missing" in request["execution_blocker_ids"]
    assert request["next_required_step"] == r50.P7_R50_R6_BLOCKED_NEXT_REQUIRED_STEP_REF
    _assert_no_runtime_or_product_completion(request)


def test_r50_r7_freezes_reviewer_instruction_and_rating_form_without_running_review_or_rows():
    freeze = r50.build_p7_r50_reviewer_instruction_rating_form_freeze(
        local_only_body_full_packet_generation_request=_r6_ready()
    )

    assert r50.assert_p7_r50_reviewer_instruction_rating_form_freeze_contract(freeze) is True
    assert freeze["schema_version"] == r50.P7_R50_REVIEWER_INSTRUCTION_RATING_FORM_FREEZE_SCHEMA_VERSION
    assert freeze["policy_section"] == "R50-7_reviewer_instruction_rating_form_freeze"
    assert freeze["request_status"] == "READY_FOR_LOCAL_ONLY_BODY_FULL_PACKET_GENERATION_REQUEST"
    assert freeze["instruction_form_status"] == "READY_FOR_REVIEWER_INSTRUCTION_AND_RATING_FORM"
    assert freeze["required_case_count"] == 24
    assert freeze["review_prompt_version"] == r50.P7_R50_REVIEW_PROMPT_VERSION
    assert freeze["reviewer_instruction_version"] == r50.P7_R50_REVIEWER_INSTRUCTION_VERSION
    assert freeze["rating_form_version"] == r50.P7_R50_RATING_FORM_VERSION
    assert freeze["reviewer_check_item_refs"] == list(r50.P7_R50_REVIEWER_CHECK_ITEM_REFS)
    assert freeze["required_reviewer_check_label_refs"] == list(r50.P7_R50_REQUIRED_REVIEWER_CHECK_LABEL_REFS)
    assert freeze["rating_axis_refs"] == [
        "history_connection_naturalness",
        "creepy_absence",
        "overclaim_absence",
        "self_blame_non_amplification",
        "wants_more_input_or_accumulation",
        "non_shallow_repeat",
    ]
    assert freeze["rating_axis_count"] == 6
    assert freeze["rating_score_min"] == 0.0
    assert freeze["rating_score_max"] == 1.0
    assert freeze["rating_score_canonical_refs"] == ["1.00", "0.75", "0.50", "0.00"]
    assert freeze["extra_rating_axis_allowed"] is False
    assert freeze["machine_auto_score_allowed"] is False
    assert freeze["rating_row_required_for_each_case"] is True
    assert freeze["verdict_refs"] == ["PASS", "YELLOW", "REPAIR_REQUIRED", "RED"]
    assert freeze["red_or_repair_requires_blocker"] is True
    assert freeze["execution_blocker_is_not_readfeel_verdict"] is True
    assert freeze["question_need_observation_selection_required"] is True
    assert freeze["question_text_required"] is False
    assert freeze["draft_question_text_allowed"] is False
    assert freeze["reviewer_free_text_local_only"] is True
    assert freeze["reviewer_free_text_bodyfree_export_allowed"] is False
    assert freeze["reviewer_free_text_to_sanitized_reason_ids_required"] is True
    assert freeze["p5_weakness_must_not_be_hidden_by_question_candidate"] is True
    assert freeze["body_full_reader_protocol_local_only"] is True
    assert freeze["blind_case_id_required"] is True
    assert freeze["case_ref_hidden_from_reviewer"] is True
    assert freeze["family_hidden_from_reviewer"] is True
    assert freeze["subscription_tier_hidden_from_reviewer"] is True
    assert freeze["controller_expected_result_hidden_from_reviewer"] is True
    assert freeze["gate_expected_result_hidden_from_reviewer"] is True
    assert freeze["reviewer_instruction_materialized_for_actual_review_here"] is False
    assert freeze["actual_rating_rows_materialized_here"] is False
    assert freeze["actual_blocker_rows_materialized_here"] is False
    assert freeze["actual_execution_blocker_rows_materialized_here"] is False
    assert freeze["actual_question_need_observation_rows_materialized_here"] is False
    assert freeze["body_full_packet_generated_here"] is False
    assert freeze["implemented_steps"] == list(r50.P7_R50_R7_IMPLEMENTED_STEPS)
    assert freeze["not_yet_implemented_steps"] == list(r50.P7_R50_R7_NOT_YET_IMPLEMENTED_STEPS)
    assert freeze["next_required_step"] == r50.P7_R50_R7_NEXT_REQUIRED_STEP_REF
    _assert_no_runtime_or_product_completion(freeze)


def test_r50_r7_blocks_reviewer_instruction_form_when_r6_request_is_blocked():
    blocked_r4 = r50.build_p7_r50_local_only_root_explicit_allow_export_denylist_preflight(
        manual_run_decision_bodyfree=_r3_go(),
        local_review_root=_VALID_LOCAL_ROOT_REF,
        explicit_allow_token="WRONG_TOKEN",
    )
    blocked_r5 = r50.build_p7_r50_review_session_protocol_bodyfree(
        local_only_root_explicit_allow_export_preflight=blocked_r4
    )
    blocked_r6 = r50.build_p7_r50_local_only_body_full_packet_generation_request(
        review_session_protocol_bodyfree=blocked_r5
    )
    freeze = r50.build_p7_r50_reviewer_instruction_rating_form_freeze(
        local_only_body_full_packet_generation_request=blocked_r6
    )

    assert freeze["request_status"] == "BLOCKED_BY_R50_5_PROTOCOL"
    assert freeze["instruction_form_status"] == "BLOCKED_BY_R50_6_PACKET_GENERATION_REQUEST"
    assert freeze["local_only_body_full_generation_allowed"] is False
    assert "r50_explicit_allow_missing" in freeze["execution_blocker_ids"]
    assert freeze["next_required_step"] == r50.P7_R50_R7_BLOCKED_NEXT_REQUIRED_STEP_REF
    _assert_no_runtime_or_product_completion(freeze)


def test_r50_r6_r7_combined_freeze_matches_nested_request_and_form():
    combined = r50.build_p7_r50_r6_r7_packet_request_rating_form_freeze(
        review_session_protocol_bodyfree=_r5_ready()
    )

    assert r50.assert_p7_r50_r6_r7_packet_request_rating_form_freeze_contract(combined) is True
    assert combined["schema_version"] == r50.P7_R50_R6_R7_PACKET_REQUEST_RATING_FORM_FREEZE_SCHEMA_VERSION
    assert combined["request_status"] == combined["r6_local_only_body_full_packet_generation_request"]["request_status"]
    assert combined["instruction_form_status"] == combined["r7_reviewer_instruction_rating_form_freeze"]["instruction_form_status"]
    assert combined["local_only_body_full_generation_allowed"] is True
    assert combined["actual_manual_review_run_here"] is False
    assert combined["body_full_packet_generated_here"] is False
    assert combined["actual_rating_rows_materialized_here"] is False
    assert combined["p7_complete"] is False
    assert combined["p8_start_allowed"] is False
    assert combined["release_allowed"] is False
    _assert_body_free_no_leak(combined)


def test_r50_r6_r7_contracts_reject_body_free_forbidden_keys():
    request = _r6_ready()
    leaked_request = copy.deepcopy(request)
    leaked_request["local_absolute_path"] = _VALID_LOCAL_ROOT_REF
    with pytest.raises(ValueError):
        r50.assert_p7_r50_local_only_body_full_packet_generation_request_contract(leaked_request)

    freeze = r50.build_p7_r50_reviewer_instruction_rating_form_freeze(
        local_only_body_full_packet_generation_request=request
    )
    leaked_freeze = copy.deepcopy(freeze)
    leaked_freeze["question_text"] = "body-free material must not include question wording"
    with pytest.raises(ValueError):
        r50.assert_p7_r50_reviewer_instruction_rating_form_freeze_contract(leaked_freeze)


def test_r50_r6_rejects_reviewer_notes_retention_drift_from_r47_contract():
    request = _r6_ready()
    drifted_request = copy.deepcopy(request)
    drifted_request["reviewer_notes_retention_after_rating_hours"] = 0

    with pytest.raises(ValueError):
        r50.assert_p7_r50_local_only_body_full_packet_generation_request_contract(drifted_request)
