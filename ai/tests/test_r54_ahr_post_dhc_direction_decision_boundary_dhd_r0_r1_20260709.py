# -*- coding: utf-8 -*-
"""R54-AHR Post-DHC direction decision boundary DHD R0/R1 tests."""

from __future__ import annotations

from copy import deepcopy

import pytest

import emlis_ai_p7_r54_ahr_post_dhb_dhr_op05_manual_call_execution_consideration_20260709 as dhc
import emlis_ai_p7_r54_ahr_post_dhc_direction_decision_boundary_20260709 as dhd
import emlis_ai_p7_r54_ahr_post_elr19_downstream_manual_decision_handoff_or_retry_20260704 as dhr


DHD_R1_FORBIDDEN_EXECUTION_KEYS = (
    "dhd_op00_implemented",
    "dhd_op01_implemented",
    "dhd_op02_implemented",
    "dhd_op03_implemented",
    "dhd_op04_implemented",
    "dhd_op05_implemented",
    "dhd_op06_implemented",
    "dhd_op07_implemented",
    "dhd_op08_implemented",
    "dhc_builder_called_here",
    "dhc_result_synthesized_here",
    "current_dhc_result_selected_here",
    "current_existing_dhr_op05_result_wrapper_selected_here",
    "dhr_op05_runtime_call_started_here",
    "existing_dhr_op05_builder_runtime_called_here",
    "dhr_op06_consideration_decided_here",
    "dhr_op06_builder_called_here",
    "dhr_op06_implicit_op05_fallback_used_here",
    "dhr_op07_materialized_here",
    "dmd_execution_started_here",
    "dmd_r52_executed_here",
    "r52_actual_execution_started_here",
    "actual_review_started_here",
    "actual_rows_created_here",
    "question_need_observation_rows_created_here",
    "p7_readfeel_reconnection_decided_here",
    "p7_readfeel_evaluation_started_here",
    "next_runtime_execution_allowed_here",
    "p8_start_allowed",
    "p8_question_design_started",
    "p8_question_implementation_started",
    "question_text_materialized_here",
    "api_changed",
    "db_changed",
    "rn_changed",
    "runtime_changed",
    "response_key_changed",
    "api_db_rn_runtime_response_key_changed",
    "json_schema_file_created",
    "p7_complete",
    "release_allowed",
    "full_backend_suite_green_claimed_here",
    "rn_contract_green_claimed_here",
    "rn_real_device_modal_verified_claimed_here",
)

DHD_R1_ALLOWED_FALSE_KEYS = (
    "dhc_builder_call_allowed_here",
    "dhc_result_synthesis_allowed_here",
    "dhc_r11_as_current_selected_result_allowed_here",
    "dhc_validation_green_as_runtime_allowed_here",
    "dhr_op05_runtime_call_allowed_here",
    "existing_dhr_op05_builder_runtime_call_allowed_here",
    "dhr_op06_consideration_decision_allowed_in_r1",
    "dhr_op06_builder_call_allowed_here",
    "dhr_op06_implicit_op05_fallback_allowed_here",
    "dhr_op07_materialization_allowed_here",
    "dmd_r52_execution_allowed_here",
    "actual_review_start_allowed_here",
    "actual_rows_creation_allowed_here",
    "question_need_observation_rows_creation_allowed_here",
    "p7_readfeel_reconnection_decision_allowed_in_r1",
    "p7_readfeel_evaluation_execution_allowed_here",
    "p8_question_design_allowed_here",
    "p8_question_implementation_allowed_here",
    "question_text_materialization_allowed_here",
    "api_db_rn_runtime_response_key_change_allowed_here",
    "json_schema_file_creation_allowed_here",
    "p7_complete_allowed_here",
    "release_decision_allowed_here",
    "full_backend_suite_green_claim_allowed_here",
    "rn_contract_green_claim_allowed_here",
    "rn_real_device_modal_verification_claim_allowed_here",
)


def _assert_dhd_r1_no_execution_or_promotion(material: dict[str, object]) -> None:
    for key in DHD_R1_FORBIDDEN_EXECUTION_KEYS:
        assert material[key] is False, key
    assert material["git_connection_required"] is False
    assert material["git_checked"] is False
    assert material["body_free"] is True


def test_dhd_r0_r1_summary_freezes_direction_boundary_and_stops_before_op00() -> None:
    summary = dhd.build_p7_r54_ahr_post_dhc_dhd_r1_helper_skeleton_constants_summary()

    assert dhd.assert_p7_r54_ahr_post_dhc_dhd_r1_helper_skeleton_constants_summary_contract(summary) is True
    assert summary["operation_step_ref"] == dhd.P7_R54_AHR_POST_DHC_DHD_R1_STEP_REF
    assert summary["boundary_prefix_ref"] == "DHD"
    assert summary["current_execution_allowance_ref"] == "none"
    assert summary["next_required_step"] == dhd.P7_R54_AHR_POST_DHC_DHD_OP00_STEP_REF
    assert tuple(summary["implemented_step_refs"]) == dhd.P7_R54_AHR_POST_DHC_DHD_R0_R1_IMPLEMENTED_STEPS
    assert tuple(summary["not_yet_implemented_step_refs"]) == dhd.P7_R54_AHR_POST_DHC_DHD_R0_R1_NOT_YET_IMPLEMENTED_STEPS
    assert tuple(summary["dhd_step_refs"]) == dhd.P7_R54_AHR_POST_DHC_DHD_STEP_REFS
    assert summary["dhc_r11_is_not_dhr_op06_permission"] is True
    assert summary["dhc_validation_green_is_not_current_runtime_execution"] is True
    assert summary["dhd_does_not_call_dhr_op06"] is True
    assert summary["dhd_does_not_start_p8"] is True
    assert summary["dhd_does_not_claim_p7_complete_or_release"] is True
    _assert_dhd_r1_no_execution_or_promotion(summary)


@pytest.mark.parametrize("key", DHD_R1_ALLOWED_FALSE_KEYS)
def test_dhd_r0_r1_keeps_all_execution_and_promotion_allowances_false(key: str) -> None:
    summary = dhd.build_p7_r54_ahr_post_dhc_dhd_r1_helper_skeleton_constants_summary()

    assert summary[key] is False, key
    assert dhd.assert_p7_r54_ahr_post_dhc_dhd_r1_helper_skeleton_constants_summary_contract(summary) is True


def test_dhd_r0_r1_records_dhc_r11_and_op08_refs_without_selecting_or_synthesizing_result() -> None:
    summary = dhd.build_p7_r54_ahr_post_dhc_dhd_r1_helper_skeleton_constants_summary()

    assert summary["dhc_r11_result_memo_ref"].endswith("DHC_R11_NextWorkDecision_20260709.md")
    assert summary["dhc_r11_recommended_next_work_candidate_ref"] == dhd.P7_R54_AHR_POST_DHC_DHD_DHC_R11_RECOMMENDED_NEXT_WORK_CANDIDATE_REF
    assert summary["dhc_op08_schema_version_ref"] == dhc.P7_R54_AHR_POST_DHB_DHC_OP08_SCHEMA_VERSION
    assert summary["dhc_op08_step_ref"] == dhc.P7_R54_AHR_POST_DHB_DHC_OP08_STEP_REF
    assert tuple(summary["dhc_op08_allowed_status_refs"]) == dhc.P7_R54_AHR_POST_DHB_DHC_OP08_ALLOWED_STATUS_REFS
    assert summary["dhc_builder_call_allowed_here"] is False
    assert summary["dhc_result_synthesis_allowed_here"] is False
    assert summary["dhc_r11_as_current_selected_result_allowed_here"] is False
    assert summary["current_dhc_result_selected_here"] is False
    assert dhd.assert_p7_r54_ahr_post_dhc_dhd_r1_helper_skeleton_constants_summary_contract(summary) is True


def test_dhd_r0_r1_keeps_dhr_op05_and_op06_as_refs_without_callables_or_fallback() -> None:
    summary = dhd.build_p7_r54_ahr_post_dhc_dhd_r1_helper_skeleton_constants_summary()

    assert summary["existing_dhr_op05_builder_ref"] == dhc.P7_R54_AHR_POST_DHB_DHC_EXISTING_DHR_OP05_BUILDER_REF
    assert summary["existing_dhr_op05_schema_version_ref"] == dhr.P7_R54_AHR_POST_ELR19_DHR_OP05_SCHEMA_VERSION
    assert summary["existing_dhr_op06_builder_ref"] == "build_p7_r54_ahr_post_elr19_dhr_op06_handoff_or_retry_deterministic_branch_resolver"
    assert summary["existing_dhr_op06_schema_version_ref"] == dhr.P7_R54_AHR_POST_ELR19_DHR_OP06_SCHEMA_VERSION
    assert tuple(summary["existing_dhr_op06_allowed_status_refs"]) == dhr.P7_R54_AHR_POST_ELR19_DHR_OP06_ALLOWED_STATUS_REFS
    assert tuple(summary["existing_dhr_op06_branch_refs"]) == dhr.P7_R54_AHR_POST_ELR19_DHR_BRANCH_REFS
    assert summary["existing_dhr_op06_implicit_op05_fallback_ref"] == "existing_DHR_OP06_builder_builds_DHR_OP05_when_explicit_OP05_material_is_none"
    assert summary["existing_dhr_op05_builder_runtime_call_allowed_here"] is False
    assert summary["dhr_op06_builder_call_allowed_here"] is False
    assert summary["dhr_op06_implicit_op05_fallback_allowed_here"] is False
    assert not hasattr(dhd, "P7_R54_AHR_POST_DHC_DHD_EXISTING_DHR_OP06_BUILDER_IMPORT_CALLABLE_REF")
    assert not hasattr(dhd, "build_p7_r54_ahr_post_elr19_dhr_op06_handoff_or_retry_deterministic_branch_resolver")
    assert dhd.assert_p7_r54_ahr_post_dhc_dhd_r1_helper_skeleton_constants_summary_contract(summary) is True


def test_dhd_r0_r1_summary_does_not_call_referenced_builders(monkeypatch: pytest.MonkeyPatch) -> None:
    def _unexpected_call(*args: object, **kwargs: object) -> dict[str, object]:
        raise AssertionError("R1 must not call DHC, DHR-OP05, or DHR-OP06 builders")

    monkeypatch.setattr(dhc, dhd.P7_R54_AHR_POST_DHC_DHD_DHC_OP08_BUILDER_REF, _unexpected_call)
    monkeypatch.setattr(dhr, dhd.P7_R54_AHR_POST_DHC_DHD_EXISTING_DHR_OP05_BUILDER_REF, _unexpected_call)
    monkeypatch.setattr(dhr, dhd.P7_R54_AHR_POST_DHC_DHD_EXISTING_DHR_OP06_BUILDER_REF, _unexpected_call)

    summary = dhd.build_p7_r54_ahr_post_dhc_dhd_r1_helper_skeleton_constants_summary()

    assert summary["dhc_op08_builder_import_available"] is True
    assert summary["existing_dhr_op05_builder_import_available"] is True
    assert summary["existing_dhr_op06_builder_import_available"] is True
    _assert_dhd_r1_no_execution_or_promotion(summary)
    assert dhd.assert_p7_r54_ahr_post_dhc_dhd_r1_helper_skeleton_constants_summary_contract(summary) is True


def test_dhd_r0_r1_exposes_exact_future_status_decision_and_stopped_closure_refs() -> None:
    summary = dhd.build_p7_r54_ahr_post_dhc_dhd_r1_helper_skeleton_constants_summary()

    assert "DHD_STATUS_DHC_OUTCOME_R11_ONLY_NO_CURRENT_SELECTED_RESULT" in summary["allowed_status_refs"]
    assert "DHD_DHC_OUTCOME_R11_ONLY_NO_CURRENT_SELECTED_RESULT" in summary["dhc_outcome_classification_refs"]
    assert "DHD_DECISION_DHR_OP06_CONSIDERATION_DESIGN_FIRST" in summary["direction_decision_refs"]
    assert "DHD_DECISION_P7_READFEEL_RECONNECTION_DESIGN_FIRST" in summary["direction_decision_refs"]
    assert "DHD_OP08_P7_READFEEL_RECONNECTION_DESIGN_CLOSED_STOPPED" in summary["allowed_status_refs"]
    assert "P7_readfeel_reconnection_product_QA_return_detailed_design" in summary["next_design_candidate_refs"]
    assert dhd.assert_p7_r54_ahr_post_dhc_dhd_r1_helper_skeleton_constants_summary_contract(summary) is True


def test_dhd_r0_r1_keeps_readfeel_reconnection_as_candidate_not_completion() -> None:
    summary = dhd.build_p7_r54_ahr_post_dhc_dhd_r1_helper_skeleton_constants_summary()

    assert "single_input_product_readfeel_and_read_feeling" in summary["p7_readfeel_axis_refs"]
    assert "continued_input_value_and_wants_to_input_again" in summary["p7_readfeel_axis_refs"]
    assert summary["expected_r11_only_direction_ref"] == "P7_readfeel_reconnection_product_QA_return_detailed_design_candidate"
    assert summary["kept_not_promoted_direction_ref"].startswith("DHR_OP06_consideration")
    assert summary["p7_readfeel_reconnection_decision_allowed_in_r1"] is False
    assert summary["p7_readfeel_evaluation_execution_allowed_here"] is False
    assert summary["p8_question_design_allowed_here"] is False
    assert summary["p7_complete"] is False
    assert summary["release_allowed"] is False
    assert dhd.assert_p7_r54_ahr_post_dhc_dhd_r1_helper_skeleton_constants_summary_contract(summary) is True


def test_dhd_r0_r1_exposes_bodyfree_no_touch_and_validation_refs() -> None:
    summary = dhd.build_p7_r54_ahr_post_dhc_dhd_r1_helper_skeleton_constants_summary()

    assert "raw_input" in summary["forbidden_payload_key_refs"]
    assert "question_text" in summary["forbidden_payload_key_refs"]
    assert "private_user_dictionary_text" in summary["forbidden_payload_key_refs"]
    assert "stdout" in summary["forbidden_payload_key_refs"]
    assert "traceback" in summary["forbidden_payload_key_refs"]
    assert "api_changed" in summary["no_touch_contract_keys"]
    assert "response_key_changed" in summary["no_touch_contract_keys"]
    assert "dhr_op06_builder_called_here" in summary["promotion_claim_field_refs"]
    assert summary["target_test_ref_refs"] == dhd.P7_R54_AHR_POST_DHC_DHD_TARGET_TEST_REF_REFS
    assert summary["compileall_target_ref_refs"] == dhd.P7_R54_AHR_POST_DHC_DHD_COMPILEALL_TARGET_REF_REFS
    assert dhd.assert_p7_r54_ahr_post_dhc_dhd_r1_helper_skeleton_constants_summary_contract(summary) is True


@pytest.mark.parametrize(
    ("mutation_key", "mutation_value"),
    [
        ("body_free", False),
        ("current_execution_allowance_ref", "DHR_OP06"),
        ("dhc_result_synthesis_allowed_here", True),
        ("dhc_r11_as_current_selected_result_allowed_here", True),
        ("dhr_op06_consideration_decision_allowed_in_r1", True),
        ("dhr_op06_builder_call_allowed_here", True),
        ("dhr_op06_implicit_op05_fallback_allowed_here", True),
        ("p7_readfeel_reconnection_decision_allowed_in_r1", True),
        ("p8_question_design_allowed_here", True),
        ("p7_complete", True),
        ("release_allowed", True),
    ],
)
def test_dhd_r0_r1_assert_rejects_execution_promotion_or_fallback_mutations(
    mutation_key: str,
    mutation_value: object,
) -> None:
    summary = dhd.build_p7_r54_ahr_post_dhc_dhd_r1_helper_skeleton_constants_summary()
    mutated = deepcopy(summary)
    mutated[mutation_key] = mutation_value

    with pytest.raises(ValueError):
        dhd.assert_p7_r54_ahr_post_dhc_dhd_r1_helper_skeleton_constants_summary_contract(mutated)


def test_dhd_r0_r1_assert_rejects_unplanned_field_addition() -> None:
    summary = dhd.build_p7_r54_ahr_post_dhc_dhd_r1_helper_skeleton_constants_summary()
    mutated = deepcopy(summary)
    mutated["unexpected_runtime_permission"] = True

    with pytest.raises(ValueError, match="field set changed"):
        dhd.assert_p7_r54_ahr_post_dhc_dhd_r1_helper_skeleton_constants_summary_contract(mutated)
