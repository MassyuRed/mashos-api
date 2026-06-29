# -*- coding: utf-8 -*-
"""R50-2/R50-3 tests for P5 human Blind QA manual-run decision.

These tests intentionally stop at prior validation evidence adoption and the
manual-review GO/NO-GO decision.  They do not generate body-full packets, run
actual human review, write rating rows, write question observation rows, touch
API/DB/RN contracts, start P8, complete P7, or claim release readiness.
"""

from __future__ import annotations

import copy

import pytest

import emlis_ai_p7_r50_p5_human_blind_qa_manual_run_decision as r50


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


def _assert_r3_no_runtime_or_product_completion(decision):
    for key in _FALSE_RUNTIME_AND_PRODUCT_FLAGS:
        assert decision[key] is False
    assert decision["body_free"] is True
    _assert_body_free_no_leak(decision)


def test_r50_r2_adopts_prior_validation_evidence_bodyfree_without_executing_commands_or_claiming_product_value():
    adoption = r50.build_p7_r50_prior_validation_evidence_adoption()

    assert r50.assert_p7_r50_prior_validation_evidence_adoption_contract(adoption) is True
    assert adoption["schema_version"] == r50.P7_R50_PRIOR_VALIDATION_EVIDENCE_ADOPTION_SCHEMA_VERSION
    assert adoption["policy_section"] == "R50-2_prior_validation_evidence_adoption"
    assert adoption["review_session_status"] == "NOT_STARTED"
    assert adoption["required_case_count"] == 24
    assert adoption["prior_validation_evidence_row_count"] == len(r50.P7_R50_PRIOR_VALIDATION_EVIDENCE_GROUP_REFS)
    assert [row["evidence_group_ref"] for row in adoption["prior_validation_evidence_rows"]] == list(
        r50.P7_R50_PRIOR_VALIDATION_EVIDENCE_GROUP_REFS
    )

    flags = adoption["precondition_flags"]
    assert flags["r49_target_green_evidence_present"] is True
    assert flags["r48_regression_green_evidence_present"] is True
    assert flags["r47_regression_green_evidence_present"] is True
    assert flags["r46_regression_green_evidence_present"] is True
    assert flags["display_p5_core_green_evidence_present"] is True
    assert flags["rn_contract_green_evidence_present"] is True
    assert flags["backend_collect_only_evidence_present"] is True
    assert flags["full_backend_suite_green_confirmed"] is False
    assert flags["collect_only_claimed_as_full_backend_green"] is False
    assert flags["rn_contract_claimed_as_real_device_modal_readfeel"] is False

    assert adoption["evidence_commands_reference_only"] is True
    assert adoption["validation_commands_executed_here"] is False
    assert adoption["command_result_body_stored_here"] is False
    assert adoption["terminal_output_stored_here"] is False
    assert adoption["manual_run_decision_made_here"] is False
    assert adoption["local_only_body_full_generation_allowed"] is False
    assert adoption["actual_manual_review_run_here"] is False
    assert adoption["body_full_packet_generated_here"] is False
    assert adoption["implemented_steps"] == list(r50.P7_R50_R2_IMPLEMENTED_STEPS)
    assert adoption["not_yet_implemented_steps"] == list(r50.P7_R50_R2_NOT_YET_IMPLEMENTED_STEPS)
    assert adoption["next_required_step"] == r50.P7_R50_R2_NEXT_REQUIRED_STEP_REF
    _assert_body_free_no_leak(adoption)


def test_r50_r3_defaults_to_no_go_before_local_root_allow_and_disposal_are_confirmed():
    adoption = r50.build_p7_r50_prior_validation_evidence_adoption()
    decision = r50.build_p7_r50_manual_run_decision_bodyfree(prior_validation_evidence_adoption=adoption)

    assert r50.assert_p7_r50_manual_run_decision_bodyfree_contract(decision) is True
    assert decision["schema_version"] == r50.P7_R50_MANUAL_RUN_DECISION_BODYFREE_SCHEMA_VERSION
    assert decision["policy_section"] == "R50-3_manual_run_go_no_go_decision_builder"
    assert decision["manual_run_decision"] == "NO_GO_LOCAL_ROOT_UNSAFE"
    assert decision["review_session_status"] == "PRECHECK_BLOCKED"
    assert decision["local_only_body_full_generation_allowed"] is False
    assert decision["execution_blocker_ids"] == ["r50_local_review_root_invalid"]
    assert decision["manual_run_decision_reason_refs"] == ["local_review_root_not_safe_or_not_confirmed"]
    assert decision["next_required_step"] == r50.P7_R50_R3_BLOCKED_NEXT_REQUIRED_STEP_REF
    assert decision["manual_run_decision_made_here"] is True
    assert decision["implemented_steps"] == list(r50.P7_R50_R2_R3_IMPLEMENTED_STEPS)
    assert decision["not_yet_implemented_steps"] == list(r50.P7_R50_R2_R3_NOT_YET_IMPLEMENTED_STEPS)
    _assert_r3_no_runtime_or_product_completion(decision)


def test_r50_r3_go_requires_all_manual_run_preconditions_but_still_does_not_generate_body_full_or_run_review():
    adoption = r50.build_p7_r50_prior_validation_evidence_adoption()
    decision = r50.build_p7_r50_manual_run_decision_bodyfree(
        prior_validation_evidence_adoption=adoption,
        local_review_root_safe=True,
        explicit_allow_present=True,
        disposal_plan_ready=True,
        body_free_summary_path_ready=True,
    )

    assert r50.assert_p7_r50_manual_run_decision_bodyfree_contract(decision) is True
    assert decision["manual_run_decision"] == "GO_FOR_LOCAL_MANUAL_REVIEW"
    assert decision["manual_run_decision_reason_refs"] == [
        "all_manual_run_preconditions_satisfied_body_full_still_not_generated"
    ]
    assert decision["review_session_status"] == "READY_FOR_LOCAL_BODY_FULL_PACKET_GENERATION"
    assert decision["local_only_body_full_generation_allowed"] is True
    assert decision["execution_blocker_ids"] == []
    assert decision["open_execution_blocker_ids"] == []
    assert decision["missing_precondition_refs"] == []
    assert decision["next_required_step"] == r50.P7_R50_R3_NEXT_REQUIRED_STEP_REF
    for flag_ref in r50.P7_R50_MANUAL_RUN_PRECONDITION_FLAG_REFS:
        assert decision["precondition_flags"][flag_ref] is True
    _assert_r3_no_runtime_or_product_completion(decision)


def test_r50_r3_missing_regression_evidence_no_go_does_not_use_go_as_product_pass():
    adoption = r50.build_p7_r50_prior_validation_evidence_adoption(
        prior_validation_evidence_overrides={
            "r48_regression": {
                "evidence_status_ref": "NOT_RUN_IN_CURRENT_R50_SESSION",
                "evidence_present": False,
                "passed_count": 0,
                "claim_boundary_ref": "missing R48 regression means no manual-run GO",
            }
        }
    )
    decision = r50.build_p7_r50_manual_run_decision_bodyfree(
        prior_validation_evidence_adoption=adoption,
        local_review_root_safe=True,
        explicit_allow_present=True,
        disposal_plan_ready=True,
        body_free_summary_path_ready=True,
    )

    assert decision["precondition_flags"]["r48_regression_green_evidence_present"] is False
    assert decision["manual_run_decision"] == "NO_GO_TARGET_OR_REGRESSION_EVIDENCE_MISSING"
    assert "missing_r48_regression_green_evidence" in decision["manual_run_decision_reason_refs"]
    assert "r50_missing_r48_regression_green_evidence" in decision["execution_blocker_ids"]
    assert decision["local_only_body_full_generation_allowed"] is False
    assert decision["p5_human_blind_qa_confirmed_candidate"] is False
    assert decision["release_allowed"] is False
    _assert_r3_no_runtime_or_product_completion(decision)


@pytest.mark.parametrize(
    ("kwargs", "expected_decision", "expected_blocker"),
    [
        (
            {"local_review_root_safe": True, "explicit_allow_present": False, "disposal_plan_ready": True, "body_free_summary_path_ready": True},
            "NO_GO_EXPLICIT_ALLOW_MISSING",
            "r50_explicit_allow_missing",
        ),
        (
            {"local_review_root_safe": True, "explicit_allow_present": True, "disposal_plan_ready": False, "body_free_summary_path_ready": True},
            "NO_GO_DISPOSAL_PLAN_UNSAFE",
            "r50_disposal_plan_missing",
        ),
        (
            {"local_review_root_safe": True, "explicit_allow_present": True, "disposal_plan_ready": True, "body_free_summary_path_ready": False},
            "NO_GO_BODY_FREE_LEAK_RISK",
            "r50_body_free_leak_detected",
        ),
        (
            {
                "local_review_root_safe": True,
                "explicit_allow_present": True,
                "disposal_plan_ready": True,
                "body_free_summary_path_ready": True,
                "body_free_leak_risk_detected": True,
            },
            "NO_GO_BODY_FREE_LEAK_RISK",
            "r50_body_free_leak_detected",
        ),
        (
            {
                "local_review_root_safe": True,
                "explicit_allow_present": True,
                "disposal_plan_ready": True,
                "body_free_summary_path_ready": True,
                "scope_drift_detected": True,
            },
            "NO_GO_SCOPE_DRIFT",
            "r50_scope_drift_detected",
        ),
    ],
)
def test_r50_r3_each_no_go_path_blocks_body_full_generation(kwargs, expected_decision, expected_blocker):
    adoption = r50.build_p7_r50_prior_validation_evidence_adoption()
    decision = r50.build_p7_r50_manual_run_decision_bodyfree(
        prior_validation_evidence_adoption=adoption,
        **kwargs,
    )

    assert decision["manual_run_decision"] == expected_decision
    assert expected_blocker in decision["execution_blocker_ids"]
    assert decision["local_only_body_full_generation_allowed"] is False
    assert decision["review_session_status"] == "PRECHECK_BLOCKED"
    assert decision["next_required_step"] == r50.P7_R50_R3_BLOCKED_NEXT_REQUIRED_STEP_REF
    _assert_r3_no_runtime_or_product_completion(decision)


def test_r50_r3_open_execution_blocker_uses_blocked_status_after_preconditions_are_met():
    adoption = r50.build_p7_r50_prior_validation_evidence_adoption()
    decision = r50.build_p7_r50_manual_run_decision_bodyfree(
        prior_validation_evidence_adoption=adoption,
        local_review_root_safe=True,
        explicit_allow_present=True,
        disposal_plan_ready=True,
        body_free_summary_path_ready=True,
        open_execution_blocker_ids=["r50_disposal_not_verified", "r50_disposal_not_verified"],
    )

    assert decision["manual_run_decision"] == "BLOCKED_BY_EXECUTION_BLOCKER"
    assert decision["review_session_status"] == "BLOCKED"
    assert decision["execution_blocker_ids"] == ["r50_disposal_not_verified"]
    assert decision["open_execution_blocker_ids"] == ["r50_disposal_not_verified"]
    assert decision["local_only_body_full_generation_allowed"] is False
    assert decision["next_required_step"] == r50.P7_R50_R3_BLOCKED_NEXT_REQUIRED_STEP_REF
    _assert_r3_no_runtime_or_product_completion(decision)


def test_r50_r2_r3_combined_freeze_matches_nested_decision_and_keeps_no_touch_boundaries():
    combined = r50.build_p7_r50_r2_r3_manual_run_decision_freeze(
        local_review_root_safe=True,
        explicit_allow_present=True,
        disposal_plan_ready=True,
        body_free_summary_path_ready=True,
    )

    assert r50.assert_p7_r50_r2_r3_manual_run_decision_freeze_contract(combined) is True
    nested_decision = combined["r3_manual_run_decision_bodyfree"]
    assert combined["schema_version"] == r50.P7_R50_R2_R3_MANUAL_RUN_DECISION_FREEZE_SCHEMA_VERSION
    assert combined["manual_run_decision"] == nested_decision["manual_run_decision"] == "GO_FOR_LOCAL_MANUAL_REVIEW"
    assert combined["local_only_body_full_generation_allowed"] is nested_decision[
        "local_only_body_full_generation_allowed"
    ]
    assert combined["implemented_steps"] == list(r50.P7_R50_R2_R3_IMPLEMENTED_STEPS)
    assert combined["not_yet_implemented_steps"] == list(r50.P7_R50_R2_R3_NOT_YET_IMPLEMENTED_STEPS)
    assert combined["manual_run_decision_made_here"] is True
    assert combined["actual_manual_review_run_here"] is False
    assert combined["body_full_packet_generated_here"] is False
    assert combined["p7_complete"] is False
    assert combined["p8_start_allowed"] is False
    assert combined["release_allowed"] is False
    _assert_body_free_no_leak(combined)


def test_r50_r2_r3_contract_rejects_body_free_forbidden_question_or_surface_keys():
    decision = r50.build_p7_r50_manual_run_decision_bodyfree(
        local_review_root_safe=True,
        explicit_allow_present=True,
        disposal_plan_ready=True,
        body_free_summary_path_ready=True,
    )
    leaked = copy.deepcopy(decision)
    leaked["question_text"] = "これはbody-freeへ残してはいけない"

    with pytest.raises(ValueError):
        r50.assert_p7_r50_manual_run_decision_bodyfree_contract(leaked)
