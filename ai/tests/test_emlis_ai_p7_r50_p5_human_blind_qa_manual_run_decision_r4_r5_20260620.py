# -*- coding: utf-8 -*-
"""R50-4/R50-5 tests for P5 human Blind QA manual-run decision.

These tests intentionally stop at the local-only preflight and the 24-case
review-session protocol.  They do not generate body-full packets, run actual
human review, write rating rows, write question observation rows, touch API/DB/RN
contracts, start P8, complete P7, or claim release readiness.
"""

from __future__ import annotations

import copy

import pytest

import emlis_ai_p7_r50_p5_human_blind_qa_manual_run_decision as r50


_VALID_LOCAL_ROOT_REF = "/tmp/cocolon_emlis_r50_local_review"
_SAFE_BODYFREE_EXPORT_CANDIDATE_REF = "summary.bodyfree/post_review_decision_summary.bodyfree.json"
_DENIED_BODYFULL_EXPORT_CANDIDATE_REF = "body_full_packets.local_only/packet_r50_001.local_only.json"

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


def _assert_no_runtime_or_product_completion(material):
    for key in _FALSE_RUNTIME_AND_PRODUCT_FLAGS:
        assert material[key] is False
    assert material["body_free"] is True
    _assert_body_free_no_leak(material)


def test_r50_r4_passes_local_only_root_allow_and_export_denylist_preflight_without_generating_body_full():
    preflight = _r4_passed()

    assert r50.assert_p7_r50_local_only_root_explicit_allow_export_denylist_preflight_contract(preflight) is True
    assert preflight["schema_version"] == r50.P7_R50_LOCAL_ONLY_ROOT_EXPLICIT_ALLOW_EXPORT_PREFLIGHT_SCHEMA_VERSION
    assert preflight["policy_section"] == "R50-4_local_only_root_explicit_allow_export_denylist_preflight"
    assert preflight["manual_run_decision"] == "GO_FOR_LOCAL_MANUAL_REVIEW"
    assert preflight["preflight_status"] == "PASSED"
    assert preflight["review_session_status"] == "READY_FOR_LOCAL_BODY_FULL_PACKET_GENERATION"
    assert preflight["local_review_root_status"] == "valid"
    assert preflight["local_review_root_valid"] is True
    assert preflight["storage_root_ref"] == "external_local_review_root"
    assert preflight["root_path_exposed"] is False
    assert preflight["local_absolute_path_included"] is False
    assert preflight["explicit_allow_token_ref"] == "LOCAL_ONLY_REVIEW_CONFIRMED"
    assert preflight["explicit_allow_present"] is True
    assert preflight["explicit_allow_token_body_stored_here"] is False
    assert preflight["export_candidate_refs_checked_count"] == 1
    assert preflight["export_candidate_refs_stored_here"] is False
    assert preflight["export_candidate_body_stored_here"] is False
    assert preflight["denied_export_candidate_count"] == 0
    assert preflight["export_denylist_violation_refs"] == []
    assert preflight["body_full_packet_export_allowed"] is False
    assert preflight["reviewer_notes_export_allowed"] is False
    assert preflight["body_full_packet_zip_inclusion_allowed"] is False
    assert preflight["premise_or_implemented_docs_inclusion_allowed"] is False
    assert preflight["local_only_body_full_generation_allowed_before_preflight"] is True
    assert preflight["local_only_body_full_generation_allowed_after_preflight"] is True
    assert preflight["local_only_body_full_generation_allowed"] is True
    assert preflight["body_full_packet_generated_here"] is False
    assert preflight["actual_human_review_run_here"] is False
    assert preflight["implemented_steps"] == list(r50.P7_R50_R4_IMPLEMENTED_STEPS)
    assert preflight["not_yet_implemented_steps"] == list(r50.P7_R50_R4_NOT_YET_IMPLEMENTED_STEPS)
    assert preflight["next_required_step"] == r50.P7_R50_R4_NEXT_REQUIRED_STEP_REF
    _assert_no_runtime_or_product_completion(preflight)


@pytest.mark.parametrize(
    ("local_review_root", "explicit_allow_token", "expected_blocker", "expected_reason"),
    [
        (None, r50.P7_R50_EXPLICIT_BODY_FULL_ALLOW_TOKEN_REF, "r50_local_review_root_missing", "local_review_root_missing"),
        ("/mnt/data/cocolon_artifact_root", r50.P7_R50_EXPLICIT_BODY_FULL_ALLOW_TOKEN_REF, "r50_local_review_root_invalid", "local_review_root_invalid"),
        (_VALID_LOCAL_ROOT_REF, "WRONG_TOKEN", "r50_explicit_allow_missing", "explicit_allow_token_missing_or_invalid"),
    ],
)
def test_r50_r4_blocks_missing_invalid_root_or_missing_explicit_allow_without_body_full_permission(
    local_review_root, explicit_allow_token, expected_blocker, expected_reason
):
    preflight = r50.build_p7_r50_local_only_root_explicit_allow_export_denylist_preflight(
        manual_run_decision_bodyfree=_r3_go(),
        local_review_root=local_review_root,
        explicit_allow_token=explicit_allow_token,
    )

    assert preflight["preflight_status"] == "BLOCKED"
    assert preflight["review_session_status"] == "PRECHECK_BLOCKED"
    assert preflight["local_only_body_full_generation_allowed_after_preflight"] is False
    assert preflight["local_only_body_full_generation_allowed"] is False
    assert expected_blocker in preflight["execution_blocker_ids"]
    assert expected_reason in preflight["preflight_reason_refs"]
    assert preflight["next_required_step"] == r50.P7_R50_R4_BLOCKED_NEXT_REQUIRED_STEP_REF
    _assert_no_runtime_or_product_completion(preflight)


def test_r50_r4_export_denylist_violation_blocks_zip_or_artifact_mixing_and_stores_counts_only():
    preflight = r50.build_p7_r50_local_only_root_explicit_allow_export_denylist_preflight(
        manual_run_decision_bodyfree=_r3_go(),
        local_review_root=_VALID_LOCAL_ROOT_REF,
        explicit_allow_token=r50.P7_R50_EXPLICIT_BODY_FULL_ALLOW_TOKEN_REF,
        export_candidate_refs=[_DENIED_BODYFULL_EXPORT_CANDIDATE_REF],
    )

    assert preflight["preflight_status"] == "BLOCKED"
    assert preflight["local_review_root_valid"] is True
    assert preflight["explicit_allow_present"] is True
    assert preflight["export_candidate_refs_checked_count"] == 1
    assert preflight["denied_export_candidate_count"] == 1
    assert "r47_export_denylist_pattern_match" in preflight["export_denylist_violation_refs"]
    assert "r50_body_full_packet_export_violation" in preflight["execution_blocker_ids"]
    assert preflight["export_candidate_refs_stored_here"] is False
    assert preflight["export_candidate_body_stored_here"] is False
    assert preflight["local_only_body_full_generation_allowed"] is False
    _assert_no_runtime_or_product_completion(preflight)


def test_r50_r5_builds_24_case_review_session_protocol_bodyfree_after_r4_passes():
    protocol = r50.build_p7_r50_review_session_protocol_bodyfree(
        local_only_root_explicit_allow_export_preflight=_r4_passed()
    )

    assert r50.assert_p7_r50_review_session_protocol_bodyfree_contract(protocol) is True
    assert protocol["schema_version"] == r50.P7_R50_REVIEW_SESSION_PROTOCOL_BODYFREE_SCHEMA_VERSION
    assert protocol["policy_section"] == "R50-5_24_case_review_session_protocol_builder"
    assert protocol["preflight_status"] == "PASSED"
    assert protocol["protocol_status"] == "READY_FOR_24_CASE_LOCAL_REVIEW_PROTOCOL"
    assert protocol["review_session_status"] == "READY_FOR_LOCAL_BODY_FULL_PACKET_GENERATION"
    assert protocol["review_prompt_version"] == r50.P7_R50_REVIEW_PROMPT_VERSION
    assert protocol["required_case_count"] == 24
    assert protocol["case_distribution_total"] == 24
    assert protocol["minimum_total_cases"] == 24
    assert protocol["minimum_per_family"] == 2
    assert protocol["minimum_history_line_eligible_input"] == 4
    assert protocol["minimum_owned_history_positive_cases"] == 12
    assert protocol["minimum_block_boundary_cases"] == {
        "low_information_history_not_eligible": 2,
        "free_tier_history_present_not_allowed": 2,
    }
    assert protocol["reviewer_visible_field_refs"] == list(r50.P7_R50_REVIEWER_VISIBLE_FIELD_REFS)
    assert protocol["reviewer_hidden_field_refs"] == list(r50.P7_R50_REVIEWER_HIDDEN_FIELD_REFS)
    assert protocol["rating_axis_refs"] == [
        "history_connection_naturalness",
        "creepy_absence",
        "overclaim_absence",
        "self_blame_non_amplification",
        "wants_more_input_or_accumulation",
        "non_shallow_repeat",
    ]
    assert protocol["question_need_observation_required"] is True
    assert protocol["rating_row_required_for_each_case"] is True
    assert protocol["execution_blocker_row_required_for_unreviewable_case"] is True
    assert protocol["question_text_required"] is False
    assert protocol["draft_question_text_allowed"] is False
    assert protocol["reviewer_free_text_bodyfree_export_allowed"] is False
    assert protocol["reviewer_free_text_local_only"] is True
    assert protocol["body_full_reader_protocol_local_only"] is True
    assert protocol["protocol_body_full_packet_generation_allowed_here"] is False
    assert protocol["protocol_human_review_run_allowed_here"] is False
    assert protocol["blind_case_id_required"] is True
    assert protocol["case_ref_hidden_from_reviewer"] is True
    assert protocol["family_hidden_from_reviewer"] is True
    assert protocol["subscription_tier_hidden_from_reviewer"] is True
    assert protocol["controller_expected_result_hidden_from_reviewer"] is True
    assert protocol["gate_expected_result_hidden_from_reviewer"] is True
    assert protocol["p5_confirmed_conditions_hidden_from_reviewer"] is True
    assert protocol["p8_material_candidate_conditions_hidden_from_reviewer"] is True
    assert protocol["implemented_steps"] == list(r50.P7_R50_R5_IMPLEMENTED_STEPS)
    assert protocol["not_yet_implemented_steps"] == list(r50.P7_R50_R5_NOT_YET_IMPLEMENTED_STEPS)
    assert protocol["next_required_step"] == r50.P7_R50_R5_NEXT_REQUIRED_STEP_REF
    _assert_no_runtime_or_product_completion(protocol)


def test_r50_r5_blocks_protocol_readiness_when_r4_preflight_is_blocked():
    blocked_r4 = r50.build_p7_r50_local_only_root_explicit_allow_export_denylist_preflight(
        manual_run_decision_bodyfree=_r3_go(),
        local_review_root=_VALID_LOCAL_ROOT_REF,
        explicit_allow_token="WRONG_TOKEN",
    )
    protocol = r50.build_p7_r50_review_session_protocol_bodyfree(
        local_only_root_explicit_allow_export_preflight=blocked_r4
    )

    assert protocol["preflight_status"] == "BLOCKED"
    assert protocol["protocol_status"] == "BLOCKED_BY_R50_4_PREFLIGHT"
    assert protocol["local_only_body_full_generation_allowed"] is False
    assert "r50_explicit_allow_missing" in protocol["execution_blocker_ids"]
    assert protocol["next_required_step"] == r50.P7_R50_R5_BLOCKED_NEXT_REQUIRED_STEP_REF
    _assert_no_runtime_or_product_completion(protocol)


def test_r50_r4_r5_combined_freeze_matches_nested_preflight_and_protocol():
    combined = r50.build_p7_r50_r4_r5_preflight_protocol_freeze(
        manual_run_decision_bodyfree=_r3_go(),
        local_review_root=_VALID_LOCAL_ROOT_REF,
        explicit_allow_token=r50.P7_R50_EXPLICIT_BODY_FULL_ALLOW_TOKEN_REF,
        export_candidate_refs=[_SAFE_BODYFREE_EXPORT_CANDIDATE_REF],
    )

    assert r50.assert_p7_r50_r4_r5_preflight_protocol_freeze_contract(combined) is True
    assert combined["schema_version"] == r50.P7_R50_R4_R5_PREFLIGHT_PROTOCOL_FREEZE_SCHEMA_VERSION
    assert combined["preflight_status"] == combined["r4_local_only_root_explicit_allow_export_denylist_preflight"]["preflight_status"] == "PASSED"
    assert combined["protocol_status"] == combined["r5_review_session_protocol_bodyfree"]["protocol_status"]
    assert combined["local_only_body_full_generation_allowed"] is True
    assert combined["actual_manual_review_run_here"] is False
    assert combined["body_full_packet_generated_here"] is False
    assert combined["p7_complete"] is False
    assert combined["p8_start_allowed"] is False
    assert combined["release_allowed"] is False
    _assert_body_free_no_leak(combined)


def test_r50_r4_r5_contracts_reject_body_free_forbidden_keys():
    preflight = _r4_passed()
    leaked_preflight = copy.deepcopy(preflight)
    leaked_preflight["local_absolute_path"] = _VALID_LOCAL_ROOT_REF
    with pytest.raises(ValueError):
        r50.assert_p7_r50_local_only_root_explicit_allow_export_denylist_preflight_contract(leaked_preflight)

    protocol = r50.build_p7_r50_review_session_protocol_bodyfree(
        local_only_root_explicit_allow_export_preflight=preflight
    )
    leaked_protocol = copy.deepcopy(protocol)
    leaked_protocol["question_text"] = "body-free protocolに質問本文を残してはいけない"
    with pytest.raises(ValueError):
        r50.assert_p7_r50_review_session_protocol_bodyfree_contract(leaked_protocol)
