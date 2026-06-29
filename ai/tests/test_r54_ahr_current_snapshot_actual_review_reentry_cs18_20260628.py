# -*- coding: utf-8 -*-
"""R54-AHR-CS18 current snapshot actual review re-entry contract tests."""

from __future__ import annotations

from copy import deepcopy
from typing import Any

import pytest

import emlis_ai_p7_r54_ahr_current_snapshot_actual_review_reentry_20260628 as cs
from test_r54_ahr_current_snapshot_actual_review_reentry_cs14_cs15_20260628 import (
    _assert_bodyfree_no_touch_allowing,
)
from test_r54_ahr_current_snapshot_actual_review_reentry_cs16_cs17_20260628 import (
    _build_ready_cs17,
)


def _green_command_matrix() -> dict[str, dict[str, str]]:
    return {
        "compileall_services_ai_inference_tests": {"status_ref": "passed"},
        "target_r54_ahr_cs00_cs18_split": {"status_ref": "passed"},
        "selected_existing_ahr_regression": {"status_ref": "passed"},
        "selected_r55_regression": {"status_ref": "passed"},
        "selected_r52_regression": {"status_ref": "passed"},
        "full_backend_suite": {"status_ref": "not_executed"},
        "rn_contract": {"status_ref": "not_executed"},
        "rn_real_device_modal": {"status_ref": "not_executed"},
    }


def _build_ready_cs18(**kwargs: Any) -> dict[str, Any]:
    material = cs.build_p7_r54_ahr_cs18_final_validation_command_matrix_documentation_output(
        candidate_handoff_envelope=_build_ready_cs17(
            p8_material_candidate_refs=(
                "question_may_reduce_overread_risk",
                "plus_single_question_candidate_later",
                "premium_deep_dive_candidate_later",
            )
        ),
        command_execution_results=_green_command_matrix(),
        **kwargs,
    )
    assert cs.assert_p7_r54_ahr_cs18_final_validation_command_matrix_documentation_output_contract(material) is True
    return material


def test_cs00_to_cs17_ready_path_is_present_before_cs18() -> None:
    cs17 = _build_ready_cs17(
        p8_material_candidate_refs=(
            "question_may_reduce_overread_risk",
            "plus_single_question_candidate_later",
            "premium_deep_dive_candidate_later",
        )
    )
    assert cs17["candidate_handoff_status_ref"] == cs.P7_R54_AHR_CS17_READY_STATUS_REF
    assert cs17["actual_review_evidence_complete"] is True
    assert cs17["p5_confirmed_candidate"] is True
    assert cs17["p5_confirmed_final"] is False
    assert cs17["p6_candidate_only_handoff_built"] is True
    assert cs17["p6_start_allowed"] is False
    assert cs17["p8_question_design_material_candidate"] is True
    assert cs17["p8_start_allowed"] is False
    assert cs17["r52_reintake_handoff_ready"] is True
    assert cs17["actual_r52_reintake_execution_confirmed"] is False
    assert cs17["next_required_step"] == cs.P7_R54_AHR_CS18_STEP_REF


def test_cs18_default_is_fail_closed_without_ready_cs17() -> None:
    material = cs.build_p7_r54_ahr_cs18_final_validation_command_matrix_documentation_output()
    assert material["final_validation_status_ref"] == cs.P7_R54_AHR_CS18_BLOCKED_STATUS_REF
    assert "cs16_p5_confirmed_candidate_not_ready_for_candidate_only_handoff" in material["execution_blocker_ids"]
    assert material["candidate_handoff_ready_for_final_validation"] is False
    assert material["actual_review_evidence_complete"] is False
    assert material["p5_confirmed_candidate"] is False
    assert material["r52_reintake_handoff_ready"] is False
    assert material["documentation_output_ready"] is False
    assert tuple(material["implemented_steps"]) == cs.P7_R54_AHR_CS17_IMPLEMENTED_STEPS
    assert tuple(material["not_yet_implemented_steps"]) == cs.P7_R54_AHR_CS17_NOT_YET_IMPLEMENTED_STEPS
    assert material["next_required_step"] == cs.P7_R54_AHR_CS18_BLOCKED_NEXT_REQUIRED_STEP_REF
    _assert_bodyfree_no_touch_allowing(material, ())
    assert cs.assert_p7_r54_ahr_cs18_final_validation_command_matrix_documentation_output_contract(material) is True


def test_cs18_ready_builds_final_validation_documentation_without_auto_promotion() -> None:
    material = _build_ready_cs18()
    assert set(material) == set(cs.P7_R54_AHR_CS18_FINAL_VALIDATION_COMMAND_MATRIX_DOCUMENTATION_OUTPUT_REQUIRED_FIELD_REFS)
    assert material["schema_version"] == cs.P7_R54_AHR_CS18_FINAL_VALIDATION_COMMAND_MATRIX_DOCUMENTATION_OUTPUT_SCHEMA_VERSION
    assert material["policy_section"] == cs.P7_R54_AHR_CS18_STEP_REF
    assert material["operation_step_ref"] == cs.P7_R54_AHR_CS18_STEP_REF
    assert material["cs17_next_required_step"] == cs.P7_R54_AHR_CS18_STEP_REF
    assert material["current_basis_ref"] == cs.P7_R54_AHR_CS_ACTUAL_REVIEW_BASIS_REF
    assert material["historical_basis_ref"] == cs.P7_R54_AHR_CS_EXISTING_AHR_BASIS_REF
    assert material["final_validation_status_ref"] == cs.P7_R54_AHR_CS18_READY_STATUS_REF
    assert material["final_validation_reason_refs"] == [cs.P7_R54_AHR_CS18_READY_REASON_REF]
    assert material["execution_blocker_ids"] == []
    assert material["open_execution_blocker_ids"] == []
    assert material["candidate_handoff_ready_for_final_validation"] is True
    assert material["required_case_count"] == 24
    assert material["reviewed_case_count"] == 24
    assert material["rating_row_count"] == 24
    assert material["question_observation_row_count"] == 24
    assert material["actual_review_evidence_complete"] is True
    assert material["actual_human_review_operation_run"] is True
    assert material["actual_human_review_executed_by_person"] is True
    assert material["actual_human_review_run_here"] is False
    assert material["actual_human_review_complete"] is False
    assert material["p5_confirmed_candidate"] is True
    assert material["p5_confirmed_candidate_not_finalized_here"] is True
    assert material["p5_human_blind_qa_confirmed_final"] is False
    assert material["p5_confirmed_final"] is False
    assert material["p5_final_allowed"] is False
    assert material["p6_candidate_only_handoff_built"] is True
    assert material["p6_limited_human_readfeel_start_allowed_candidate"] is True
    assert material["p6_limited_human_readfeel_start_allowed"] is False
    assert material["p6_start_allowed"] is False
    assert material["p8_material_candidate_only_handoff_built"] is True
    assert material["p8_question_design_material_candidate"] is True
    assert material["p8_material_candidate_refs"] == [
        "question_may_reduce_overread_risk",
        "plus_single_question_candidate_later",
        "premium_deep_dive_candidate_later",
    ]
    assert material["p8_material_candidate_ref_count"] == 3
    assert material["p8_material_candidate_question_text_included"] is False
    assert material["p8_material_candidate_draft_question_text_included"] is False
    assert material["p8_material_candidate_question_answer_persistence_started"] is False
    assert material["p8_start_allowed"] is False
    assert material["r52_reintake_handoff_envelope_built"] is True
    assert material["r52_reintake_handoff_ready"] is True
    assert material["r52_reintake_handoff_ready_here"] is True
    assert material["r52_reintake_execution_requested_here"] is False
    assert material["actual_r52_reintake_execution_confirmed"] is False
    assert material["p7_complete"] is False
    assert material["release_allowed"] is False
    assert material["command_matrix_row_count"] == len(cs.P7_R54_AHR_CS18_COMMAND_REFS)
    assert tuple(material["command_matrix_command_refs"]) == cs.P7_R54_AHR_CS18_COMMAND_REFS
    assert material["command_matrix_passed_refs"] == list(cs.P7_R54_AHR_CS18_COMMAND_GREEN_EVIDENCE_ACCEPTABLE_REFS)
    assert material["command_matrix_green_evidence_accepted_refs"] == list(cs.P7_R54_AHR_CS18_COMMAND_GREEN_EVIDENCE_ACCEPTABLE_REFS)
    assert material["command_matrix_not_executed_refs"] == list(cs.P7_R54_AHR_CS18_COMMAND_NOT_FULL_SCOPE_REFS)
    assert material["command_matrix_failed_refs"] == []
    assert material["command_matrix_timeout_killed_interrupted_refs"] == []
    assert material["command_matrix_output_body_included_refs"] == []
    assert material["command_matrix_bodyfree_only"] is True
    assert material["command_matrix_no_unexecuted_passed_claim"] is True
    assert material["command_matrix_no_timeout_kill_interrupted_green_claim"] is True
    assert material["command_matrix_no_output_body_included"] is True
    assert material["full_backend_suite_green_confirmed"] is False
    assert material["rn_contract_green_confirmed"] is False
    assert material["rn_real_device_modal_verified"] is False
    assert material["selected_regression_green_not_full_backend_suite_green"] is True
    assert material["rn_contract_green_not_real_device_modal_verified"] is True
    assert tuple(material["claim_boundary_refs"]) == cs.P7_R54_AHR_CS18_CLAIM_BOUNDARY_REFS
    assert material["claim_boundary_ref_count"] == len(cs.P7_R54_AHR_CS18_CLAIM_BOUNDARY_REFS)
    assert material["documentation_output_bodyfree_only"] is True
    assert material["documentation_output_ready"] is True
    assert material["documentation_output_claims_no_auto_promotion"] is True
    assert tuple(material["implemented_steps"]) == cs.P7_R54_AHR_CS18_IMPLEMENTED_STEPS
    assert tuple(material["not_yet_implemented_steps"]) == cs.P7_R54_AHR_CS18_NOT_YET_IMPLEMENTED_STEPS
    assert material["next_required_step"] == cs.P7_R54_AHR_CS18_READY_NEXT_REQUIRED_STEP_REF
    _assert_bodyfree_no_touch_allowing(material, cs.P7_R54_AHR_CS18_ALLOWED_TRUE_FALSE_FLAG_REFS)


@pytest.mark.parametrize(
    "flag_name",
    (
        "actual_human_review_run_here",
        "actual_human_review_complete",
        "p5_human_blind_qa_confirmed_final",
        "p5_confirmed_final",
        "p5_final_allowed",
        "p6_limited_human_readfeel_start_allowed",
        "p6_start_allowed",
        "p8_material_candidate_question_text_included",
        "p8_material_candidate_draft_question_text_included",
        "p8_material_candidate_question_answer_persistence_started",
        "p8_start_allowed",
        "r52_reintake_execution_requested_here",
        "actual_r52_reintake_execution_confirmed",
        "p7_complete",
        "release_allowed",
        "full_backend_suite_green_confirmed",
        "rn_contract_green_confirmed",
        "rn_real_device_modal_verified",
    ),
)
def test_cs18_rejects_mutated_final_start_execution_or_unconfirmed_green_flags(flag_name: str) -> None:
    material = deepcopy(_build_ready_cs18())
    material[flag_name] = True
    with pytest.raises(ValueError):
        cs.assert_p7_r54_ahr_cs18_final_validation_command_matrix_documentation_output_contract(material)


def test_cs18_rejects_unexecuted_passed_command_claim() -> None:
    material = deepcopy(_build_ready_cs18())
    material["command_matrix_rows"][0]["command_executed"] = False
    with pytest.raises(ValueError):
        cs.assert_p7_r54_ahr_cs18_final_validation_command_matrix_documentation_output_contract(material)


@pytest.mark.parametrize(
    "status_field",
    (
        "command_timeout",
        "command_killed",
        "command_interrupted",
    ),
)
def test_cs18_rejects_runtime_bad_command_as_green_evidence(status_field: str) -> None:
    material = deepcopy(_build_ready_cs18())
    row = material["command_matrix_rows"][0]
    row[status_field] = True
    row["command_green_evidence_accepted"] = True
    with pytest.raises(ValueError):
        cs.assert_p7_r54_ahr_cs18_final_validation_command_matrix_documentation_output_contract(material)


@pytest.mark.parametrize(
    "body_flag",
    (
        "command_output_body_included",
        "stdout_body_included",
        "stderr_body_included",
        "traceback_body_included",
        "terminal_output_body_included",
        "local_absolute_path_included",
        "body_hash_included",
    ),
)
def test_cs18_rejects_command_output_path_or_hash_body_flags(body_flag: str) -> None:
    material = deepcopy(_build_ready_cs18())
    material["command_matrix_rows"][0][body_flag] = True
    with pytest.raises(ValueError):
        cs.assert_p7_r54_ahr_cs18_final_validation_command_matrix_documentation_output_contract(material)


def test_cs18_blocks_when_selected_green_command_times_out_in_builder_input() -> None:
    commands = _green_command_matrix()
    commands["selected_existing_ahr_regression"] = {"status_ref": "timeout"}
    material = cs.build_p7_r54_ahr_cs18_final_validation_command_matrix_documentation_output(
        candidate_handoff_envelope=_build_ready_cs17(p8_material_candidate_refs=("question_may_reduce_overread_risk",)),
        command_execution_results=commands,
    )
    assert material["final_validation_status_ref"] == cs.P7_R54_AHR_CS18_BLOCKED_STATUS_REF
    assert "command_matrix_has_timeout_killed_or_interrupted_refs" in material["execution_blocker_ids"]
    assert material["command_matrix_timeout_killed_interrupted_refs"] == ["selected_existing_ahr_regression"]
    assert material["documentation_output_ready"] is False
    assert cs.assert_p7_r54_ahr_cs18_final_validation_command_matrix_documentation_output_contract(material) is True


def test_cs18_aliases_match_primary_builder_and_contract() -> None:
    primary = _build_ready_cs18()
    alias = cs.build_p7_r54_ahr_current_snapshot_actual_review_reentry_final_validation_documentation_bodyfree(
        candidate_handoff_envelope=_build_ready_cs17(
            p8_material_candidate_refs=(
                "question_may_reduce_overread_risk",
                "plus_single_question_candidate_later",
                "premium_deep_dive_candidate_later",
            )
        ),
        command_execution_results=_green_command_matrix(),
    )
    assert alias == primary
    assert cs.assert_p7_r54_ahr_current_snapshot_actual_review_reentry_final_validation_documentation_bodyfree_contract(alias) is True
    assert cs.assert_p7_r54_ahr_cs18_final_no_body_leak_no_question_text_no_touch_validation_contract(alias) is True
    assert cs.assert_p7_r54_ahr_cs18_validation_command_matrix_documentation_output_contract(alias) is True
