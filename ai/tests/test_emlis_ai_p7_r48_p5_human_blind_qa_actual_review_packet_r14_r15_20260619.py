# -*- coding: utf-8 -*-
"""R48 R14/R15 R46 handoff and P5 core subset regression freeze."""

from __future__ import annotations

import emlis_ai_p7_r48_p5_human_blind_qa_actual_review_packet as r48


def _r12_r13_freeze() -> dict:
    freeze = r48.build_p7_r48_r12_r13_confirmed_gate_leak_guard_freeze()
    assert r48.assert_p7_r48_r12_r13_confirmed_gate_leak_guard_freeze_contract(freeze)
    return freeze


def _r14_policy() -> dict:
    policy = r48.build_p7_r48_r46_handoff_regression_policy(r12_r13_freeze=_r12_r13_freeze())
    assert r48.assert_p7_r48_r46_handoff_regression_policy_contract(policy)
    return policy


def test_r0_to_r13_existing_freeze_is_present_before_r14_r15() -> None:
    freeze = _r12_r13_freeze()

    assert freeze["p5_confirmed_candidate_gate_ready"] is True
    assert freeze["no_body_free_leak_guard_ready"] is True
    assert freeze["r47_target_regression_required"] is True
    assert freeze["next_required_step"] == "R14_r46_handoff_regression"
    assert freeze["p5_human_blind_qa_confirmed"] is False
    assert freeze["p6_limited_human_readfeel_start_allowed"] is False
    assert freeze["actual_human_review_run_here"] is False
    assert freeze["actual_body_full_packet_generated_here"] is False
    assert freeze["release_allowed"] is False


def test_r14_policy_requires_r46_regression_without_claiming_execution() -> None:
    policy = _r14_policy()

    assert policy["r46_handoff_regression_required"] is True
    assert policy["r46_p5_p6_handoff_regression_required"] is True
    assert policy["r46_real_device_closed_validation_regression_required"] is True
    assert policy["r46_next_decision_ledger_regression_required"] is True
    assert tuple(policy["r46_handoff_regression_test_refs"]) == r48.P7_R48_R46_HANDOFF_REGRESSION_TEST_REFS
    assert policy["r46_handoff_regression_executed_here"] is False
    assert policy["actual_r46_handoff_regression_executed_here"] is False
    assert policy["r46_contract_builders_checked_here"] is True
    assert policy["next_required_step"] == "R15_p5_core_subset_regression"


def test_r14_policy_refreezes_r46_hold_state_and_release_boundary() -> None:
    policy = _r14_policy()

    assert set(r48.P7_R48_REQUIRED_UNRESOLVED_HOLD_REFS) <= set(policy["unresolved_hold_refs"])
    assert policy["p5_human_blind_qa_start_allowed_after_r46_ledger"] is True
    assert policy["p5_human_blind_qa_confirmed"] is False
    assert policy["p6_limited_human_readfeel_start_allowed"] is False
    assert policy["p6_limited_human_readfeel_confirmed"] is False
    assert policy["real_device_modal_review_start_allowed"] is False
    assert policy["real_device_modal_review_confirmed"] is False
    assert policy["human_review_confirmed"] is False
    assert policy["manual_real_device_review_confirmed"] is False
    assert policy["release_allowed"] is False
    assert policy["p7_complete"] is False
    assert policy["p8_start_allowed"] is False
    assert policy["hold004_close_allowed"] is False


def test_r14_policy_keeps_only_schema_and_material_refs_body_free() -> None:
    policy = _r14_policy()

    assert set(policy["r46_schema_version_refs"]) == {
        "p5_human_blind_qa_handoff",
        "p6_limited_human_readfeel_handoff",
        "p5_p6_human_readfeel_handoff_summary",
        "real_device_modal_review_checklist",
        "hold_release_p8_closed_validation",
        "real_device_and_closed_validation_summary",
        "next_decision_summary",
        "next_decision_handoff_ledger",
    }
    assert set(policy["r46_material_refs"]) == {
        "p5_material_ref",
        "p6_material_ref",
        "p5_p6_summary_ref",
        "real_device_summary_ref",
        "next_decision_summary_ref",
        "next_decision_ledger_ref",
    }
    assert r48.assert_p7_r48_no_body_free_leak_guard_bodyfree_material(policy, source="r14_policy")


def test_r15_policy_requires_p5_core_subset_without_runtime_or_green_claim() -> None:
    r14 = _r14_policy()
    policy = r48.build_p7_r48_p5_core_subset_regression_policy(r46_handoff_regression_policy=r14)

    assert r48.assert_p7_r48_p5_core_subset_regression_policy_contract(policy)
    assert policy["p5_core_subset_regression_required"] is True
    assert tuple(policy["p5_core_subset_regression_test_refs"]) == r48.P7_R48_P5_CORE_SUBSET_REGRESSION_TEST_REFS
    assert tuple(policy["p5_product_quality_qa_optional_regression_test_refs"]) == r48.P7_R48_P5_PRODUCT_QUALITY_QA_OPTIONAL_REGRESSION_TEST_REFS
    assert policy["p5_product_quality_qa_required_here"] is False
    assert policy["p5_core_subset_regression_executed_here"] is False
    assert policy["actual_p5_core_subset_regression_executed_here"] is False
    assert policy["p5_core_subset_green_confirmed_here"] is False
    assert policy["p5_core_subset_green_claim_allowed"] is False
    assert policy["next_required_step"] == "R16_display_contract_rn_no_touch_confirmation"


def test_r15_policy_keeps_p5_runtime_api_db_gate_and_release_no_touch() -> None:
    r14 = _r14_policy()
    policy = r48.build_p7_r48_p5_core_subset_regression_policy(r46_handoff_regression_policy=r14)

    assert policy["p5_existing_boundary_preserved_required"] is True
    assert policy["p5_runtime_changed_here"] is False
    assert policy["p5_gate_relaxed_here"] is False
    assert policy["api_response_shape_changed_here"] is False
    assert policy["db_schema_changed_here"] is False
    assert policy["emlis_reply_runtime_changed_here"] is False
    assert policy["public_response_top_level_key_added_here"] is False
    assert policy["rn_contract_changed_here"] is False
    assert policy["p5_human_blind_qa_confirmed"] is False
    assert policy["p6_limited_human_readfeel_start_allowed"] is False
    assert policy["real_device_modal_review_start_allowed"] is False
    assert policy["release_allowed"] is False
    assert policy["p7_complete"] is False
    assert policy["p8_start_allowed"] is False
    assert policy["hold004_close_allowed"] is False


def test_r14_r15_combined_freeze_keeps_review_and_release_closed_and_points_to_r16() -> None:
    freeze = r48.build_p7_r48_r14_r15_regression_freeze(r12_r13_freeze=_r12_r13_freeze())

    assert r48.assert_p7_r48_r14_r15_regression_freeze_contract(freeze)
    assert freeze["r46_handoff_regression_required"] is True
    assert freeze["p5_core_subset_regression_required"] is True
    assert freeze["r46_handoff_regression_executed_here"] is False
    assert freeze["p5_core_subset_regression_executed_here"] is False
    assert freeze["p5_core_subset_green_confirmed_here"] is False
    assert freeze["p5_runtime_changed_here"] is False
    assert freeze["p5_gate_relaxed_here"] is False
    assert freeze["p5_human_blind_qa_confirmed"] is False
    assert freeze["p6_limited_human_readfeel_start_allowed"] is False
    assert freeze["real_device_modal_review_start_allowed"] is False
    assert freeze["actual_human_review_run_here"] is False
    assert freeze["actual_body_full_packet_generated_here"] is False
    assert freeze["body_full_writer_created_here"] is False
    assert freeze["release_allowed"] is False
    assert freeze["p7_complete"] is False
    assert freeze["p8_start_allowed"] is False
    assert freeze["hold004_close_allowed"] is False
    assert freeze["next_required_step"] == "R16_display_contract_rn_no_touch_confirmation"
    assert tuple(freeze["implemented_steps"]) == r48.P7_R48_R14_R15_IMPLEMENTED_STEPS
    assert tuple(freeze["not_yet_implemented_steps"]) == r48.P7_R48_R14_R15_NOT_YET_IMPLEMENTED_STEPS
