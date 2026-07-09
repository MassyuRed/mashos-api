# -*- coding: utf-8 -*-
"""R54-AHR Post-DHB DHR-OP05 manual call execution consideration DHC R0/R1 tests."""

from __future__ import annotations

from copy import deepcopy
from pathlib import Path
import sys

import pytest

TEST_DIR = Path(__file__).resolve().parent
if str(TEST_DIR) not in sys.path:
    sys.path.insert(0, str(TEST_DIR))

import emlis_ai_p7_r54_ahr_post_dhb_dhr_op05_manual_call_execution_consideration_20260709 as dhc
import emlis_ai_p7_r54_ahr_post_elr19_downstream_manual_decision_handoff_or_retry_20260704 as dhr
import emlis_ai_p7_r54_ahr_post_pcm_dhr_op05_manual_handoff_boundary_20260708 as dhb


DHC_R1_FORBIDDEN_EXECUTION_KEYS = (
    "dhc_op00_implemented",
    "dhc_op01_implemented",
    "dhc_op02_implemented",
    "dhc_op03_implemented",
    "dhc_op04_implemented",
    "dhc_op05_implemented",
    "dhc_op06_implemented",
    "dhc_op07_implemented",
    "dhc_op08_implemented",
    "dhb_op08_material_synthesized_here",
    "dhb_builder_called_here",
    "dhb_r11_memo_used_as_dhb_op08_here",
    "dhb_handoff_envelope_used_as_dhr_op04_input_here",
    "existing_dhr_op04_assert_called_here",
    "implicit_op04_builder_fallback_allowed_here",
    "implicit_op04_builder_fallback_used_here",
    "manual_call_requested_here",
    "manual_call_allowed_here",
    "existing_dhr_op05_builder_call_allowed_here",
    "existing_dhr_op05_builder_called_here",
    "existing_dhr_op05_result_present",
    "existing_dhr_op05_contract_valid",
    "dhr_op05_called_here",
    "dhr_op05_builder_called_here",
    "dhr_op06_called_here",
    "dhr_op07_materialized_here",
    "dmd_execution_started_here",
    "dmd_r52_executed_here",
    "r52_actual_execution_started_here",
    "actual_review_started_here",
    "actual_rows_created_here",
    "question_need_observation_rows_created_here",
    "raw_evidence_request_created_here",
    "repair_executed_here",
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
    "json_schema_file_created_here",
    "p7_complete",
    "release_allowed",
    "full_backend_suite_green_claimed_here",
    "rn_contract_green_claimed_here",
    "rn_real_device_modal_verified_claimed_here",
)


_ALLOWED_FALSE_KEYS = (
    "dhb_op08_material_synthesis_allowed_here",
    "dhb_builder_call_allowed_here",
    "dhb_r11_memo_as_dhb_op08_allowed_here",
    "dhb_handoff_envelope_as_dhr_op04_input_allowed_here",
    "existing_dhr_op04_assert_call_allowed_in_r1",
    "implicit_op04_builder_fallback_allowed_here",
    "implicit_op04_builder_fallback_used_here",
    "manual_call_requested_here",
    "manual_call_permission_allowed_here",
    "existing_dhr_op05_builder_call_allowed_here",
    "existing_dhr_op05_builder_called_here",
    "existing_dhr_op05_result_present",
    "existing_dhr_op05_contract_valid",
    "dhr_op05_call_allowed_here",
    "dhr_op05_builder_call_allowed_here",
    "dhr_op06_call_allowed_here",
    "dhr_op07_materialization_allowed_here",
    "dmd_r52_execution_allowed_here",
    "actual_review_start_allowed_here",
    "actual_rows_creation_allowed_here",
    "question_need_observation_rows_creation_allowed_here",
    "repair_execution_allowed_here",
    "raw_evidence_request_allowed_here",
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
    "full_backend_suite_green_confirmed",
    "rn_contract_green_confirmed",
    "rn_real_device_modal_verified_claimed_here",
)


def _assert_dhc_r1_no_downstream_execution(material: dict[str, object]) -> None:
    for key in DHC_R1_FORBIDDEN_EXECUTION_KEYS:
        assert material[key] is False, key
    assert material["git_connection_required"] is False
    assert material["git_checked"] is False
    assert material["body_free"] is True


def test_dhc_r0_r1_summary_freezes_scope_and_stops_before_op00() -> None:
    summary = dhc.build_p7_r54_ahr_post_dhb_dhc_r1_helper_skeleton_constants_summary()

    assert dhc.assert_p7_r54_ahr_post_dhb_dhc_r1_helper_skeleton_constants_summary_contract(summary) is True
    assert summary["operation_step_ref"] == dhc.P7_R54_AHR_POST_DHB_DHC_R1_STEP_REF
    assert summary["boundary_prefix_ref"] == "DHC"
    assert summary["next_required_step"] == dhc.P7_R54_AHR_POST_DHB_DHC_OP00_STEP_REF
    assert tuple(summary["implemented_step_refs"]) == dhc.P7_R54_AHR_POST_DHB_DHC_R0_R1_IMPLEMENTED_STEPS
    assert tuple(summary["not_yet_implemented_step_refs"]) == dhc.P7_R54_AHR_POST_DHB_DHC_R0_R1_NOT_YET_IMPLEMENTED_STEPS
    assert tuple(summary["dhc_step_refs"]) == dhc.P7_R54_AHR_POST_DHB_DHC_STEP_REFS
    assert summary["explicit_dhb_op08_closed_material_required"] is True
    assert summary["dhc_op00_implemented"] is False
    assert summary["dhc_op08_implemented"] is False
    _assert_dhc_r1_no_downstream_execution(summary)


@pytest.mark.parametrize("key", _ALLOWED_FALSE_KEYS)
def test_dhc_r0_r1_keeps_execution_p8_release_and_contract_flags_false(key: str) -> None:
    summary = dhc.build_p7_r54_ahr_post_dhb_dhc_r1_helper_skeleton_constants_summary()

    assert summary[key] is False, key
    assert dhc.assert_p7_r54_ahr_post_dhb_dhc_r1_helper_skeleton_constants_summary_contract(summary) is True


def test_dhc_r0_r1_records_dhb_op08_refs_without_synthesis_or_dhb_builder_call() -> None:
    summary = dhc.build_p7_r54_ahr_post_dhb_dhc_r1_helper_skeleton_constants_summary()

    assert summary["allowed_dhb_op08_schema_version_ref"] == dhb.P7_R54_AHR_POST_PCM_DHB_OP08_SCHEMA_VERSION
    assert summary["allowed_dhb_op08_step_ref"] == dhb.P7_R54_AHR_POST_PCM_DHB_OP08_STEP_REF
    assert summary["allowed_dhb_op08_closed_status_ref"] == dhb.P7_R54_AHR_POST_PCM_DHB_OP08_ALLOWED_STATUS_REFS[0]
    assert summary["dhb_dhr_op05_lane_ref"] == dhb.P7_R54_AHR_POST_PCM_DHB_DHR_OP05_LANE_REF
    assert summary["dhb_op08_material_synthesis_allowed_here"] is False
    assert summary["dhb_builder_call_allowed_here"] is False
    assert summary["dhb_r11_memo_as_dhb_op08_allowed_here"] is False
    assert dhc.assert_p7_r54_ahr_post_dhb_dhc_r1_helper_skeleton_constants_summary_contract(summary) is True


def test_dhc_r0_r1_separates_dhb_handoff_envelope_from_dhr_op04_actual_source_claim() -> None:
    summary = dhc.build_p7_r54_ahr_post_dhb_dhc_r1_helper_skeleton_constants_summary()

    assert summary["dhb_op04_handoff_envelope_step_ref"] == dhb.P7_R54_AHR_POST_PCM_DHB_OP04_STEP_REF
    assert summary["existing_dhr_op04_schema_version_ref"] == dhr.P7_R54_AHR_POST_ELR19_DHR_OP04_SCHEMA_VERSION
    assert summary["existing_dhr_op04_step_ref"] == dhr.P7_R54_AHR_POST_ELR19_DHR_OP04_STEP_REF
    assert summary["dhb_handoff_envelope_as_dhr_op04_input_allowed_here"] is False
    assert summary["explicit_dhr_op04_actual_source_claim_separation_required"] is True
    assert summary["implicit_op04_builder_fallback_allowed_here"] is False
    assert summary["implicit_op04_builder_fallback_used_here"] is False
    assert dhc.assert_p7_r54_ahr_post_dhb_dhc_r1_helper_skeleton_constants_summary_contract(summary) is True


def test_dhc_r0_r1_records_existing_dhr_op05_string_and_import_refs_without_calling_builder() -> None:
    summary = dhc.build_p7_r54_ahr_post_dhb_dhc_r1_helper_skeleton_constants_summary()

    assert summary["existing_dhr_op05_builder_ref"] == dhc.P7_R54_AHR_POST_DHB_DHC_EXISTING_DHR_OP05_BUILDER_REF
    assert summary["existing_dhr_op05_builder_import_path_ref"] == dhc.P7_R54_AHR_POST_DHB_DHC_EXISTING_DHR_OP05_BUILDER_IMPORT_PATH_REF
    assert summary["existing_dhr_op05_builder_import_available"] is True
    assert dhc.P7_R54_AHR_POST_DHB_DHC_EXISTING_DHR_OP05_BUILDER_IMPORT_CALLABLE_REF is dhr.build_p7_r54_ahr_post_elr19_dhr_op05_bodyfree_leak_promotion_claim_dmd_compatibility_preflight_scan
    assert summary["existing_dhr_op05_assert_ref"] == dhc.P7_R54_AHR_POST_DHB_DHC_EXISTING_DHR_OP05_ASSERT_REF
    assert summary["existing_dhr_op05_assert_import_available"] is True
    assert tuple(summary["existing_dhr_op05_allowed_status_refs"]) == dhr.P7_R54_AHR_POST_ELR19_DHR_OP05_ALLOWED_STATUS_REFS
    assert summary["existing_dhr_op05_builder_call_allowed_here"] is False
    assert summary["existing_dhr_op05_builder_called_here"] is False
    assert summary["existing_dhr_op05_result_present"] is False
    assert dhc.assert_p7_r54_ahr_post_dhb_dhc_r1_helper_skeleton_constants_summary_contract(summary) is True


def test_dhc_r0_r1_exposes_guard_refs_for_future_bodyfree_scan() -> None:
    summary = dhc.build_p7_r54_ahr_post_dhb_dhc_r1_helper_skeleton_constants_summary()

    assert "question_text" in summary["forbidden_payload_key_refs"]
    assert "stdout" in summary["forbidden_payload_key_refs"]
    assert "traceback" in summary["forbidden_payload_key_refs"]
    assert "api_changed" in summary["no_touch_contract_keys"]
    assert "response_key_changed" in summary["no_touch_contract_keys"]
    assert "existing_dhr_op05_builder_called_here" in summary["promotion_claim_field_refs"]
    assert "dhr_op06_called_here" in summary["promotion_claim_field_refs"]
    assert "release_allowed" in summary["promotion_claim_field_refs"]
    assert dhc.assert_p7_r54_ahr_post_dhb_dhc_r1_helper_skeleton_constants_summary_contract(summary) is True


@pytest.mark.parametrize(
    ("mutation_key", "mutation_value"),
    [
        ("body_free", False),
        ("dhb_op08_material_synthesis_allowed_here", True),
        ("dhb_handoff_envelope_as_dhr_op04_input_allowed_here", True),
        ("implicit_op04_builder_fallback_allowed_here", True),
        ("manual_call_permission_allowed_here", True),
        ("existing_dhr_op05_builder_call_allowed_here", True),
        ("existing_dhr_op05_builder_called_here", True),
        ("dhr_op06_call_allowed_here", True),
        ("api_db_rn_runtime_response_key_change_allowed_here", True),
        ("release_decision_allowed_here", True),
        ("release_allowed", True),
    ],
)
def test_dhc_r0_r1_assert_rejects_execution_promotion_or_fallback_mutations(
    mutation_key: str,
    mutation_value: object,
) -> None:
    summary = dhc.build_p7_r54_ahr_post_dhb_dhc_r1_helper_skeleton_constants_summary()
    mutated = deepcopy(summary)
    mutated[mutation_key] = mutation_value

    with pytest.raises(ValueError):
        dhc.assert_p7_r54_ahr_post_dhb_dhc_r1_helper_skeleton_constants_summary_contract(mutated)
