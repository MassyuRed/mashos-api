# -*- coding: utf-8 -*-
"""R54-AHR Post-PCM DHR-OP05 manual handoff boundary DHB R0/R1 tests."""

from __future__ import annotations

from copy import deepcopy
from pathlib import Path
import sys

import pytest

TEST_DIR = Path(__file__).resolve().parent
if str(TEST_DIR) not in sys.path:
    sys.path.insert(0, str(TEST_DIR))

import emlis_ai_p7_r54_ahr_post_pcm_dhr_op05_manual_handoff_boundary_20260708 as dhb


DHB_R1_FORBIDDEN_EXECUTION_KEYS = (
    "pcm_op08_material_synthesized_here",
    "pcm_builder_called_here",
    "pcm_r11_memo_used_as_current_lane_here",
    "pcm_target_green_used_as_current_lane_here",
    "pcm_decision_table_used_as_single_lane_here",
    "dhr_op05_called_here",
    "dhr_op05_builder_called_here",
    "existing_dhr_op05_builder_called_here",
    "dhr_op06_called_here",
    "dhr_op07_materialized_here",
    "dmd_execution_started_here",
    "r52_actual_execution_started_here",
    "actual_review_started_here",
    "actual_rows_created_here",
    "question_need_observation_rows_created_here",
    "raw_evidence_request_created_here",
    "repair_executed_here",
    "p8_start_allowed",
    "p8_question_design_started",
    "p8_question_implementation_started",
    "question_text_materialized",
    "api_changed",
    "db_changed",
    "rn_changed",
    "runtime_changed",
    "response_key_changed",
    "json_schema_file_created_here",
    "p7_complete",
    "release_allowed",
    "full_backend_suite_green_claimed_here",
    "rn_contract_green_claimed_here",
    "rn_real_device_modal_verified_claimed_here",
)


def _assert_dhb_r1_no_downstream_execution(material: dict[str, object]) -> None:
    for key in DHB_R1_FORBIDDEN_EXECUTION_KEYS:
        assert material[key] is False, key
    assert material["git_connection_required"] is False
    assert material["git_checked"] is False
    assert material["body_free"] is True


_ALLOWED_FALSE_KEYS = (
    "pcm_op08_material_synthesis_allowed_here",
    "pcm_builder_call_allowed_here",
    "pcm_r11_memo_as_current_lane_allowed_here",
    "pcm_target_green_as_current_lane_allowed_here",
    "pcm_decision_table_as_single_lane_allowed_here",
    "dhr_op05_call_allowed_here",
    "dhr_op05_builder_call_allowed_here",
    "existing_dhr_op05_builder_call_allowed_here",
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


def test_dhb_r0_r1_summary_freezes_scope_and_stops_before_op00() -> None:
    summary = dhb.build_p7_r54_ahr_post_pcm_dhb_r1_helper_skeleton_constants_summary()

    assert dhb.assert_p7_r54_ahr_post_pcm_dhb_r1_helper_skeleton_constants_summary_contract(summary) is True
    assert summary["operation_step_ref"] == dhb.P7_R54_AHR_POST_PCM_DHB_R1_STEP_REF
    assert summary["next_required_step"] == dhb.P7_R54_AHR_POST_PCM_DHB_OP00_STEP_REF
    assert tuple(summary["implemented_step_refs"]) == dhb.P7_R54_AHR_POST_PCM_DHB_R0_R1_IMPLEMENTED_STEPS
    assert tuple(summary["not_yet_implemented_step_refs"]) == dhb.P7_R54_AHR_POST_PCM_DHB_R0_R1_NOT_YET_IMPLEMENTED_STEPS
    assert tuple(summary["dhb_step_refs"]) == dhb.P7_R54_AHR_POST_PCM_DHB_STEP_REFS
    assert summary["explicit_pcm_op08_closed_material_required"] is True
    assert summary["dhb_op00_implemented"] is False
    assert summary["dhb_op08_implemented"] is False
    _assert_dhb_r1_no_downstream_execution(summary)


@pytest.mark.parametrize("key", _ALLOWED_FALSE_KEYS)
def test_dhb_r0_r1_keeps_execution_p8_release_and_contract_flags_false(key: str) -> None:
    summary = dhb.build_p7_r54_ahr_post_pcm_dhb_r1_helper_skeleton_constants_summary()

    assert summary[key] is False, key
    assert dhb.assert_p7_r54_ahr_post_pcm_dhb_r1_helper_skeleton_constants_summary_contract(summary) is True


def test_dhb_r0_r1_records_existing_dhr_op05_refs_without_calling_or_importing_builder() -> None:
    summary = dhb.build_p7_r54_ahr_post_pcm_dhb_r1_helper_skeleton_constants_summary()

    assert summary["existing_dhr_op05_builder_ref"] == dhb.P7_R54_AHR_POST_PCM_DHB_EXISTING_DHR_OP05_BUILDER_REF
    assert summary["existing_dhr_op05_assert_ref"] == dhb.P7_R54_AHR_POST_PCM_DHB_EXISTING_DHR_OP05_ASSERT_REF
    assert summary["existing_dhr_op05_builder_call_allowed_here"] is False
    assert summary["existing_dhr_op05_builder_called_here"] is False
    assert not hasattr(dhb, "dhr")
    assert dhb.assert_p7_r54_ahr_post_pcm_dhb_r1_helper_skeleton_constants_summary_contract(summary) is True


def test_dhb_r0_r1_keeps_pcm_op08_explicit_material_boundary_without_lane_inference() -> None:
    summary = dhb.build_p7_r54_ahr_post_pcm_dhb_r1_helper_skeleton_constants_summary()

    assert summary["allowed_pcm_op08_schema_version_ref"] == dhb.P7_R54_AHR_POST_PCM_DHB_ALLOWED_PCM_OP08_SCHEMA_VERSION_REF
    assert summary["allowed_pcm_op08_step_ref"] == dhb.P7_R54_AHR_POST_PCM_DHB_ALLOWED_PCM_OP08_STEP_REF
    assert summary["allowed_pcm_op08_closed_status_ref"] == dhb.P7_R54_AHR_POST_PCM_DHB_ALLOWED_PCM_OP08_CLOSED_STATUS_REF
    assert summary["dhr_op05_lane_ref"] == dhb.P7_R54_AHR_POST_PCM_DHB_DHR_OP05_LANE_REF
    assert summary["pcm_r11_memo_as_current_lane_allowed_here"] is False
    assert summary["pcm_target_green_as_current_lane_allowed_here"] is False
    assert summary["pcm_decision_table_as_single_lane_allowed_here"] is False
    assert dhb.assert_p7_r54_ahr_post_pcm_dhb_r1_helper_skeleton_constants_summary_contract(summary) is True


def test_dhb_r0_r1_exposes_guard_refs_for_future_bodyfree_scan() -> None:
    summary = dhb.build_p7_r54_ahr_post_pcm_dhb_r1_helper_skeleton_constants_summary()

    assert "question_text" in summary["forbidden_payload_key_refs"]
    assert "stdout" in summary["forbidden_payload_key_refs"]
    assert "traceback" in summary["forbidden_payload_key_refs"]
    assert "api_changed" in summary["no_touch_contract_keys"]
    assert "response_key_changed" in summary["no_touch_contract_keys"]
    assert "dhr_op05_called_here" in summary["promotion_claim_field_refs"]
    assert "release_allowed" in summary["promotion_claim_field_refs"]
    assert dhb.assert_p7_r54_ahr_post_pcm_dhb_r1_helper_skeleton_constants_summary_contract(summary) is True


@pytest.mark.parametrize(
    ("mutation_key", "mutation_value"),
    [
        ("body_free", False),
        ("dhr_op05_call_allowed_here", True),
        ("existing_dhr_op05_builder_call_allowed_here", True),
        ("api_db_rn_runtime_response_key_change_allowed_here", True),
        ("release_decision_allowed_here", True),
        ("dhr_op05_called_here", True),
        ("release_allowed", True),
    ],
)
def test_dhb_r0_r1_assert_rejects_execution_or_promotion_mutations(
    mutation_key: str,
    mutation_value: object,
) -> None:
    summary = dhb.build_p7_r54_ahr_post_pcm_dhb_r1_helper_skeleton_constants_summary()
    mutated = deepcopy(summary)
    mutated[mutation_key] = mutation_value

    with pytest.raises(ValueError):
        dhb.assert_p7_r54_ahr_post_pcm_dhb_r1_helper_skeleton_constants_summary_contract(mutated)
