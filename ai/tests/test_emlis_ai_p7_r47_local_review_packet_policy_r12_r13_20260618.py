# -*- coding: utf-8 -*-
"""P7-R47 R12/R13 R46 ledger connection and contract-test policy freeze."""

from __future__ import annotations

import copy
import json

import pytest

from emlis_ai_p7_r46_next_decision_handoff_ledger import (
    BRANCH_A_DISPLAY_GREEN_LINEAGE_CONSISTENT,
    build_p7_r46_next_decision_handoff_ledger,
)
from emlis_ai_p7_r47_local_review_packet_policy import (
    P7_R47_CONTRACT_TEST_POLICY_SCHEMA_VERSION,
    P7_R47_R12_NEXT_RECOMMENDED_WORK_AFTER_POLICY_REFS,
    P7_R47_R12_POLICY_READY_SUMMARY_FIELD_REFS,
    P7_R47_R12_R13_IMPLEMENTED_STEPS,
    P7_R47_R12_R13_LEDGER_CONTRACT_TEST_POLICY_SCHEMA_VERSION,
    P7_R47_R12_R13_NEXT_REQUIRED_STEP_REF,
    P7_R47_R12_R13_NOT_YET_IMPLEMENTED_STEPS,
    P7_R47_R13_REQUIRED_CONTRACT_TEST_REFS,
    P7_R47_R13_TARGET_TEST_MODULE_REFS,
    P7_R47_R46_NEXT_DECISION_LEDGER_CONNECTION_POLICY_SCHEMA_VERSION,
    assert_p7_r47_contract_test_policy_contract,
    assert_p7_r47_r12_r13_ledger_contract_test_policy_freeze_contract,
    assert_p7_r47_r46_next_decision_ledger_connection_policy_contract,
    build_p7_r47_contract_test_policy,
    build_p7_r47_r12_r13_ledger_contract_test_policy_freeze,
    build_p7_r47_r46_next_decision_ledger_connection_policy,
)

SECRET_INPUT = "R47 R12/R13 raw input must never enter body-free handoff material"
SECRET_COMMENT = "R47 R12/R13 comment text body must remain local-only"
SECRET_SURFACE = "R47 R12/R13 reviewer surface must remain local-only"
SECRET_NOTE = "R47 R12/R13 reviewer note must remain local-only"


def _dumped(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def _assert_no_body_or_release_promotion(value: object) -> None:
    dumped = _dumped(value)
    assert SECRET_INPUT not in dumped
    assert SECRET_COMMENT not in dumped
    assert SECRET_SURFACE not in dumped
    assert SECRET_NOTE not in dumped
    assert '"raw_input":' not in dumped
    assert '"comment_text":' not in dumped
    assert '"candidate_body":' not in dumped
    assert '"surface_body":' not in dumped
    assert '"surface_for_reviewer":' not in dumped
    assert '"reviewer_free_text":' not in dumped
    assert '"reviewer_notes":' not in dumped
    assert '"terminal_output":' not in dumped
    assert '"body_content_hash":' not in dumped
    assert '"release_allowed": true' not in dumped.lower()
    assert '"p7_complete": true' not in dumped.lower()
    assert '"p8_start_allowed": true' not in dumped.lower()
    assert '"hold004_close_allowed": true' not in dumped.lower()


def test_r47_r12_connects_to_r46_branch_a_without_mutating_ledger_and_opens_only_p5_start_path() -> None:
    policy = build_p7_r47_r46_next_decision_ledger_connection_policy()
    assert_p7_r47_r46_next_decision_ledger_connection_policy_contract(policy)

    assert policy["schema_version"] == P7_R47_R46_NEXT_DECISION_LEDGER_CONNECTION_POLICY_SCHEMA_VERSION
    assert policy["r46_next_decision_branch_ref"] == BRANCH_A_DISPLAY_GREEN_LINEAGE_CONSISTENT
    assert tuple(policy["r46_next_order_from_ledger"]) == (
        "local_review_packet_storage_generation_disposal_policy",
        *P7_R47_R12_NEXT_RECOMMENDED_WORK_AFTER_POLICY_REFS,
    )
    assert tuple(policy["next_recommended_work_after_r47_policy_refs"]) == P7_R47_R12_NEXT_RECOMMENDED_WORK_AFTER_POLICY_REFS
    assert policy["next_recommended_work_ref"] == "p5_human_blind_qa_material_generation_and_review"
    assert policy["p5_human_blind_qa_next_work_ref"] == "p5_human_blind_qa_material_generation_and_review"
    assert policy["p6_limited_human_readfeel_queued_after_p5_ref"] == "p6_limited_human_readfeel_review_after_p5"
    assert policy["real_device_modal_review_queued_after_p5_p6_ref"] == "real_device_submit_modal_readfeel_review"

    assert policy["r46_ledger_mutation_required"] is False
    assert policy["r46_ledger_mutated_here"] is False
    assert policy["r46_ledger_write_required"] is False
    assert policy["r46_ledger_body_free_reference_only"] is True
    assert policy["r47_summary_is_new_body_free_material"] is True

    assert policy["r47_policy_ready"] is True
    assert policy["local_review_packet_policy_ready"] is True
    assert policy["policy_ready"] is True
    assert policy["p5_human_blind_qa_start_allowed_after_policy"] is True
    assert policy["p5_human_blind_qa_start_allowed_after_r12"] is True
    assert policy["p5_human_blind_qa_confirmed"] is False
    assert policy["p6_limited_human_readfeel_start_allowed"] is False
    assert policy["p6_limited_human_readfeel_confirmed"] is False
    assert policy["real_device_modal_review_start_allowed"] is False
    assert policy["real_device_modal_review_queued_after_p5_p6"] is True
    assert policy["real_device_modal_review_confirmed"] is False
    assert policy["release_allowed"] is False
    assert policy["p7_complete"] is False
    assert policy["p8_start_allowed"] is False
    assert policy["hold004_close_allowed"] is False
    _assert_no_body_or_release_promotion(policy)


def test_r47_r12_policy_summary_has_fixed_ready_and_closed_fields() -> None:
    policy = build_p7_r47_r46_next_decision_ledger_connection_policy()
    summary = policy["r47_policy_summary"]

    assert tuple(policy["r47_policy_summary_field_refs"]) == P7_R47_R12_POLICY_READY_SUMMARY_FIELD_REFS
    assert set(summary) == set(P7_R47_R12_POLICY_READY_SUMMARY_FIELD_REFS) | {
        "p6_limited_human_readfeel_confirmed",
        "real_device_modal_review_queued_after_p5_p6",
        "real_device_modal_review_confirmed",
        "body_free",
    }
    assert summary["r47_policy_ready"] is True
    assert summary["p5_human_blind_qa_start_allowed_after_policy"] is True
    assert summary["p5_human_blind_qa_confirmed"] is False
    assert summary["p6_limited_human_readfeel_start_allowed"] is False
    assert summary["real_device_modal_review_start_allowed"] is False
    assert summary["release_allowed"] is False
    assert summary["p7_complete"] is False
    assert summary["p8_start_allowed"] is False
    assert summary["hold004_close_allowed"] is False
    assert summary["body_free"] is True


@pytest.mark.parametrize(
    ("key", "value"),
    [
        ("raw_input", SECRET_INPUT),
        ("comment_text", SECRET_COMMENT),
        ("surface_for_reviewer", SECRET_SURFACE),
        ("reviewer_free_text", SECRET_NOTE),
        ("terminal_output", "terminal output must not enter R12"),
        ("body_content_hash", "hash-of-body-must-not-enter-r12"),
        ("release_allowed", True),
        ("p7_complete", True),
        ("p8_start_allowed", True),
        ("hold004_close_allowed", True),
        ("p5_human_blind_qa_confirmed", True),
        ("p6_limited_human_readfeel_start_allowed", True),
        ("real_device_modal_review_start_allowed", True),
        ("actual_human_review_run_here", True),
    ],
)
def test_r47_r12_rejects_body_keys_release_promotion_or_review_promotion(key: str, value: object) -> None:
    policy = build_p7_r47_r46_next_decision_ledger_connection_policy()
    policy[key] = value
    with pytest.raises(ValueError):
        assert_p7_r47_r46_next_decision_ledger_connection_policy_contract(policy)


def test_r47_r12_rejects_non_branch_a_or_mutated_next_order() -> None:
    ledger = build_p7_r46_next_decision_handoff_ledger()
    wrong_branch = copy.deepcopy(ledger)
    wrong_branch["next_decision_summary"]["active_decision_branch"] = "B_DISPLAY_GREEN_PUBLIC_LINEAGE_YELLOW"
    with pytest.raises(ValueError):
        build_p7_r47_r46_next_decision_ledger_connection_policy(r46_next_decision_ledger=wrong_branch)

    wrong_order = copy.deepcopy(ledger)
    wrong_order["next_decision_summary"]["next_recommended_work_refs"] = [
        "p5_human_blind_qa_material_generation_and_review",
        "local_review_packet_storage_generation_disposal_policy",
        "p6_limited_human_readfeel_review_after_p5",
        "real_device_submit_modal_readfeel_review",
    ]
    with pytest.raises(ValueError):
        build_p7_r47_r46_next_decision_ledger_connection_policy(r46_next_decision_ledger=wrong_order)


def test_r47_r13_contract_test_policy_freezes_required_test_matrix_without_claiming_execution_green() -> None:
    policy = build_p7_r47_contract_test_policy()
    assert_p7_r47_contract_test_policy_contract(policy)

    assert policy["schema_version"] == P7_R47_CONTRACT_TEST_POLICY_SCHEMA_VERSION
    assert tuple(policy["required_contract_test_refs"]) == P7_R47_R13_REQUIRED_CONTRACT_TEST_REFS
    assert policy["required_contract_test_count"] == 12
    assert tuple(policy["target_test_module_refs"]) == P7_R47_R13_TARGET_TEST_MODULE_REFS
    assert policy["target_test_module_refs"][-1] == "tests/test_emlis_ai_p7_r47_local_review_packet_policy_r12_r13_20260618.py"

    assert policy["body_free_contract_tests_required"] is True
    assert policy["storage_root_contract_tests_required"] is True
    assert policy["body_full_schema_local_only_contract_test_required"] is True
    assert policy["body_free_manifest_contract_test_required"] is True
    assert policy["body_free_rating_blocker_contract_test_required"] is True
    assert policy["disposal_receipt_body_free_contract_test_required"] is True
    assert policy["p5_r46_alignment_contract_test_required"] is True
    assert policy["p6_r46_alignment_contract_test_required"] is True
    assert policy["real_device_rn_api_db_boundary_contract_test_required"] is True
    assert policy["release_p7_p8_hold004_closed_contract_test_required"] is True

    assert policy["contract_test_file_materialized_here"] is True
    assert policy["actual_contract_test_execution_claimed_here"] is False
    assert policy["full_backend_suite_green_claimed_here"] is False
    assert policy["full_backend_suite_execution_green_confirmed"] is False
    assert policy["rn_contract_execution_claimed_here"] is False
    assert policy["real_device_execution_claimed_here"] is False
    assert policy["body_full_packet_generation_claimed_here"] is False
    assert policy["human_review_execution_claimed_here"] is False

    assert policy["r47_policy_ready"] is True
    assert policy["p5_human_blind_qa_start_allowed_after_policy"] is True
    assert policy["p5_human_blind_qa_confirmed"] is False
    assert policy["p6_limited_human_readfeel_start_allowed"] is False
    assert policy["real_device_modal_review_start_allowed"] is False
    assert policy["release_allowed"] is False
    assert policy["p7_complete"] is False
    assert policy["p8_start_allowed"] is False
    assert policy["hold004_close_allowed"] is False
    assert policy["next_required_step"] == P7_R47_R12_R13_NEXT_REQUIRED_STEP_REF
    _assert_no_body_or_release_promotion(policy)


@pytest.mark.parametrize(
    "required_ref",
    [
        "policy_builder_body_free_release_closed",
        "missing_storage_root_denies_body_full_generation",
        "repo_docs_tests_services_mnt_data_roots_rejected",
        "body_free_manifest_rejects_body_and_reviewer_payload_keys",
        "body_free_rating_row_rejects_reviewer_text_comment_text_terminal_output",
        "disposal_receipt_rejects_body_content_hash",
        "p5_policy_matches_r46_families_axes_thresholds",
        "p6_policy_matches_r46_families_no_connect_axes_thresholds",
        "p6_start_blocked_before_p5_human_review_confirmed",
        "real_device_policy_preserves_rn_api_db_public_shape",
        "release_p7_p8_hold004_remain_closed",
        "body_full_local_packet_schema_marked_local_only_and_rejected_as_body_free_p7_material",
    ],
)
def test_r47_r13_required_contract_test_refs_cover_design_required_items(required_ref: str) -> None:
    policy = build_p7_r47_contract_test_policy()
    assert required_ref in policy["required_contract_test_refs"]


@pytest.mark.parametrize(
    ("key", "value"),
    [
        ("raw_input", SECRET_INPUT),
        ("comment_text", SECRET_COMMENT),
        ("surface_for_reviewer", SECRET_SURFACE),
        ("reviewer_free_text", SECRET_NOTE),
        ("terminal_output", "terminal output must not enter R13"),
        ("body_content_hash", "hash-of-body-must-not-enter-r13"),
        ("release_allowed", True),
        ("p7_complete", True),
        ("p8_start_allowed", True),
        ("hold004_close_allowed", True),
        ("p5_human_blind_qa_confirmed", True),
        ("p6_limited_human_readfeel_start_allowed", True),
        ("real_device_modal_review_start_allowed", True),
        ("actual_contract_test_execution_claimed_here", True),
        ("full_backend_suite_green_claimed_here", True),
        ("human_review_execution_claimed_here", True),
    ],
)
def test_r47_r13_rejects_body_keys_release_promotion_or_execution_claims(key: str, value: object) -> None:
    policy = build_p7_r47_contract_test_policy()
    policy[key] = value
    with pytest.raises(ValueError):
        assert_p7_r47_contract_test_policy_contract(policy)


def test_r47_r12_r13_combined_freeze_marks_policy_ready_but_keeps_actual_reviews_and_release_closed() -> None:
    freeze = build_p7_r47_r12_r13_ledger_contract_test_policy_freeze()
    assert_p7_r47_r12_r13_ledger_contract_test_policy_freeze_contract(freeze)

    assert freeze["schema_version"] == P7_R47_R12_R13_LEDGER_CONTRACT_TEST_POLICY_SCHEMA_VERSION
    assert tuple(freeze["implemented_steps"]) == P7_R47_R12_R13_IMPLEMENTED_STEPS
    assert freeze["implemented_steps"][-2:] == [
        "R12_r46_next_decision_ledger_connection",
        "R13_r47_contract_test_policy",
    ]
    assert tuple(freeze["not_yet_implemented_steps"]) == P7_R47_R12_R13_NOT_YET_IMPLEMENTED_STEPS
    assert freeze["not_yet_implemented_steps"] == [
        "R14_target_validation_command_matrix",
        "R15_touch_candidate_and_no_touch_boundary",
    ]
    assert freeze["next_required_step"] == P7_R47_R12_R13_NEXT_REQUIRED_STEP_REF

    assert freeze["r46_ledger_connection_policy_fixed"] is True
    assert freeze["contract_test_policy_fixed"] is True
    assert freeze["r47_policy_ready"] is True
    assert freeze["local_review_packet_policy_ready"] is True
    assert freeze["policy_ready"] is True
    assert freeze["p5_human_blind_qa_start_allowed_after_policy"] is True
    assert freeze["p5_human_blind_qa_start_allowed_after_r12_r13"] is True
    assert freeze["p5_human_blind_qa_confirmed"] is False
    assert freeze["p6_limited_human_readfeel_start_allowed"] is False
    assert freeze["real_device_modal_review_start_allowed"] is False
    assert freeze["real_device_modal_review_queued_after_p5_p6"] is True
    assert freeze["actual_human_review_run_here"] is False
    assert freeze["actual_real_device_review_run_here"] is False
    assert freeze["actual_body_full_packet_generated_here"] is False
    assert freeze["actual_contract_test_execution_claimed_here"] is False
    assert freeze["full_backend_suite_execution_green_confirmed"] is False
    assert freeze["release_allowed"] is False
    assert freeze["p7_complete"] is False
    assert freeze["p8_start_allowed"] is False
    assert freeze["hold004_close_allowed"] is False
    assert freeze["next_recommended_work_ref"] == "p5_human_blind_qa_material_generation_and_review"
    assert freeze["required_contract_test_count"] == len(P7_R47_R13_REQUIRED_CONTRACT_TEST_REFS)
    _assert_no_body_or_release_promotion(freeze)


@pytest.mark.parametrize(
    ("key", "value"),
    [
        ("raw_input", SECRET_INPUT),
        ("comment_text", SECRET_COMMENT),
        ("surface_for_reviewer", SECRET_SURFACE),
        ("reviewer_free_text", SECRET_NOTE),
        ("terminal_output", "terminal output must not enter combined R12/R13"),
        ("body_content_hash", "hash-of-body-must-not-enter-combined-r12-r13"),
        ("release_allowed", True),
        ("p7_complete", True),
        ("p8_start_allowed", True),
        ("hold004_close_allowed", True),
        ("p5_human_blind_qa_confirmed", True),
        ("p6_limited_human_readfeel_start_allowed", True),
        ("real_device_modal_review_start_allowed", True),
        ("actual_human_review_run_here", True),
        ("actual_real_device_review_run_here", True),
        ("actual_contract_test_execution_claimed_here", True),
        ("full_backend_suite_green_claimed_here", True),
    ],
)
def test_r47_r12_r13_combined_freeze_rejects_body_keys_release_review_or_execution_claims(key: str, value: object) -> None:
    freeze = build_p7_r47_r12_r13_ledger_contract_test_policy_freeze()
    freeze[key] = value
    with pytest.raises(ValueError):
        assert_p7_r47_r12_r13_ledger_contract_test_policy_freeze_contract(freeze)
