# -*- coding: utf-8 -*-
"""R54-AHR Post-PCM DHR-OP05 manual handoff boundary DHB OP04/OP05 tests."""

from __future__ import annotations

from copy import deepcopy
from pathlib import Path
import sys

import pytest

TEST_DIR = Path(__file__).resolve().parent
if str(TEST_DIR) not in sys.path:
    sys.path.insert(0, str(TEST_DIR))

import emlis_ai_p7_r54_ahr_post_pcm_dhr_op05_manual_handoff_boundary_20260708 as dhb


_DHB_OP04_FALSE_CLAIM_KEYS = (
    "existing_dhr_op05_builder_call_allowed_here",
    "existing_dhr_op05_builder_called_here",
    "dhr_op05_call_allowed_here",
    "dhr_op05_builder_call_allowed_here",
    "selected_pcm_next_boundary_execution_allowed_here",
    "dhr_op06_call_allowed_here",
    "dhr_op07_materialization_allowed_here",
    "dmd_r52_execution_allowed_here",
    "actual_review_start_allowed_here",
    "actual_rows_creation_allowed_here",
    "question_need_observation_rows_creation_allowed_here",
    "raw_evidence_request_allowed_here",
    "repair_execution_allowed_here",
    "p8_question_design_allowed_here",
    "p8_question_implementation_allowed_here",
    "question_text_materialization_allowed_here",
    "api_db_rn_runtime_response_key_change_allowed_here",
    "json_schema_file_creation_allowed_here",
    "p7_complete_allowed_here",
    "release_decision_allowed_here",
    "dhr_op05_handoff_envelope_is_builder_input",
    "dhr_op05_handoff_envelope_is_execution_result",
    "dhr_op05_called_here",
    "dhr_op05_builder_called_here",
    "dhr_op06_called_here",
    "dhr_op07_materialized_here",
    "dmd_execution_started_here",
    "r52_actual_execution_started_here",
    "actual_review_started_here",
    "actual_rows_created_here",
    "question_need_observation_rows_created_here",
    "p8_question_design_started",
    "p8_question_implementation_started",
    "p7_complete",
    "release_allowed",
)

_DHB_OP05_FALSE_CLAIM_KEYS = (
    "existing_dhr_op05_builder_call_allowed_here",
    "existing_dhr_op05_builder_called_here",
    "existing_dhr_op05_status_generated_here",
    "existing_dhr_op05_clear_status_generated_here",
    "dhr_op05_result_generated_here",
    "dhr_op05_preflight_scan_executed_here",
    "dhr_op05_builder_input_materialized_here",
    "dhr_op05_call_allowed_here",
    "dhr_op05_builder_call_allowed_here",
    "selected_pcm_next_boundary_execution_allowed_here",
    "dhr_op06_call_allowed_here",
    "dhr_op07_materialization_allowed_here",
    "dmd_r52_execution_allowed_here",
    "actual_review_start_allowed_here",
    "actual_rows_creation_allowed_here",
    "question_need_observation_rows_creation_allowed_here",
    "raw_evidence_request_allowed_here",
    "repair_execution_allowed_here",
    "p8_question_design_allowed_here",
    "p8_question_implementation_allowed_here",
    "question_text_materialization_allowed_here",
    "api_db_rn_runtime_response_key_change_allowed_here",
    "json_schema_file_creation_allowed_here",
    "p7_complete_allowed_here",
    "release_decision_allowed_here",
    "dhr_op05_called_here",
    "dhr_op05_builder_called_here",
    "dhr_op06_called_here",
    "dhr_op07_materialized_here",
    "dmd_execution_started_here",
    "r52_actual_execution_started_here",
    "actual_review_started_here",
    "actual_rows_created_here",
    "question_need_observation_rows_created_here",
    "p8_question_design_started",
    "p8_question_implementation_started",
    "p7_complete",
    "release_allowed",
)


def _explicit_pcm_op08_material(**overrides: object) -> dict[str, object]:
    material: dict[str, object] = {
        "schema_version": dhb.P7_R54_AHR_POST_PCM_DHB_ALLOWED_PCM_OP08_SCHEMA_VERSION_REF,
        "operation_step_ref": dhb.P7_R54_AHR_POST_PCM_DHB_ALLOWED_PCM_OP08_STEP_REF,
        "material_id": "explicit_pcm_op08_dhr_op05_lane_bodyfree_closure_material_for_dhb_op04_op05_test",
        "review_session_id": "dhb_op04_op05_test_session",
        "body_free": True,
        "pcm_op08_status_ref": dhb.P7_R54_AHR_POST_PCM_DHB_ALLOWED_PCM_OP08_CLOSED_STATUS_REF,
        "bodyfree_post_pnt_closed_material_confirmation_closure_status_ref": dhb.P7_R54_AHR_POST_PCM_DHB_ALLOWED_PCM_OP08_CLOSED_STATUS_REF,
        "pcm_op08_closed_stopped": True,
        "selected_pnt_lane_ref": dhb.P7_R54_AHR_POST_PCM_DHB_DHR_OP05_LANE_REF,
        "selected_pcm_next_work_class_ref": dhb.P7_R54_AHR_POST_PCM_DHB_EXPECTED_SELECTED_PCM_NEXT_WORK_CLASS_REF,
        "selected_pcm_next_boundary_ref": dhb.P7_R54_AHR_POST_PCM_DHB_EXPECTED_SELECTED_PCM_NEXT_BOUNDARY_REF,
        "selected_pcm_next_boundary_kind_ref": dhb.P7_R54_AHR_POST_PCM_DHB_EXPECTED_SELECTED_PCM_NEXT_BOUNDARY_KIND_REF,
        "selected_pcm_next_boundary_not_executed": True,
        "selected_pcm_next_boundary_execution_allowed_here": False,
        "next_design_document_candidate_ref": dhb.P7_R54_AHR_POST_PCM_DHB_EXPECTED_NEXT_DESIGN_DOCUMENT_CANDIDATE_REF,
        "next_design_document_allowed": True,
        "dhr_op05_call_allowed_here": False,
        "dhr_op05_builder_call_allowed_here": False,
        "dhr_op06_call_allowed_here": False,
        "dmd_r52_execution_allowed_here": False,
        "actual_review_start_allowed_here": False,
        "raw_evidence_request_allowed_here": False,
        "repair_execution_allowed_here": False,
        "p8_question_design_allowed_here": False,
        "api_db_rn_response_key_change_allowed_here": False,
        "json_schema_file_creation_allowed_here": False,
        "pnt_op08_builder_not_called": True,
        "pnt_op08_material_not_synthesized": True,
        "dhr_op05_not_called": True,
        "dhr_op06_not_called": True,
        "dmd_r52_not_executed": True,
        "actual_review_not_started": True,
        "p5_p6_p8_p7_release_not_started": True,
        "p8_question_design_not_started": True,
        "p8_question_implementation_not_started": True,
        "api_db_rn_runtime_response_key_not_changed": True,
    }
    material.update(overrides)
    return material


def _op00() -> dict[str, object]:
    return dhb.build_p7_r54_ahr_post_pcm_dhb_op00_scope_no_execution_refreeze_after_pcm_r11()


def _op01(**material_overrides: object) -> dict[str, object]:
    return dhb.build_p7_r54_ahr_post_pcm_dhb_op01_explicit_pcm_op08_closed_material_intake(
        explicit_pcm_op08_closed_material=_explicit_pcm_op08_material(**material_overrides),
        op00_scope_refreeze=_op00(),
    )


def _op02(**material_overrides: object) -> dict[str, object]:
    return dhb.build_p7_r54_ahr_post_pcm_dhb_op02_pcm_op08_contract_validation(_op01(**material_overrides))


def _op03(**material_overrides: object) -> dict[str, object]:
    return dhb.build_p7_r54_ahr_post_pcm_dhb_op03_dhr_op05_lane_exact_confirmation(_op02(**material_overrides))


def _op04(**material_overrides: object) -> dict[str, object]:
    return dhb.build_p7_r54_ahr_post_pcm_dhb_op04_dhr_op05_manual_handoff_envelope_without_call(_op03(**material_overrides))


def _op05(**material_overrides: object) -> dict[str, object]:
    return dhb.build_p7_r54_ahr_post_pcm_dhb_op05_existing_dhr_op05_compatibility_crosswalk_without_call(_op04(**material_overrides))


def test_dhb_op04_materializes_handoff_envelope_only_for_confirmed_dhr_lane() -> None:
    op04 = _op04()

    assert dhb.assert_p7_r54_ahr_post_pcm_dhb_op04_dhr_op05_manual_handoff_envelope_without_call_contract(op04) is True
    assert op04["operation_step_ref"] == dhb.P7_R54_AHR_POST_PCM_DHB_OP04_STEP_REF
    assert op04["dhb_op04_status_ref"] == dhb.P7_R54_AHR_POST_PCM_DHB_OP04_ALLOWED_STATUS_REFS[0]
    assert op04["dhr_op05_lane_confirmed"] is True
    assert op04["dhr_op05_manual_handoff_envelope_materialized"] is True
    assert op04["dhr_op05_handoff_envelope_ready"] is True
    assert op04["dhr_op05_preflight_reentry_candidate_allowed"] is True
    assert op04["dhr_op05_call_still_requires_separate_explicit_instruction"] is True
    assert op04["dhr_op05_handoff_envelope_is_builder_input"] is False
    assert op04["dhr_op05_handoff_envelope_is_execution_result"] is False
    assert op04["existing_dhr_op05_builder_ref"] == dhb.P7_R54_AHR_POST_PCM_DHB_EXISTING_DHR_OP05_BUILDER_REF
    assert op04["existing_dhr_op05_assert_ref"] == dhb.P7_R54_AHR_POST_PCM_DHB_EXISTING_DHR_OP05_ASSERT_REF
    assert op04["existing_dhr_op05_builder_called_here"] is False
    assert op04["next_required_step"] == dhb.P7_R54_AHR_POST_PCM_DHB_OP05_STEP_REF
    assert tuple(op04["implemented_steps"]) == dhb.P7_R54_AHR_POST_PCM_DHB_OP04_IMPLEMENTED_STEPS
    assert tuple(op04["not_yet_implemented_steps"]) == dhb.P7_R54_AHR_POST_PCM_DHB_OP04_NOT_YET_IMPLEMENTED_STEPS


def test_dhb_op04_does_not_call_existing_dhr_builder_even_when_callable_is_present(monkeypatch: pytest.MonkeyPatch) -> None:
    called = {"value": False}

    def fake_builder(*args: object, **kwargs: object) -> dict[str, object]:
        called["value"] = True
        return {"unexpected": True}

    monkeypatch.setattr(dhb, dhb.P7_R54_AHR_POST_PCM_DHB_EXISTING_DHR_OP05_BUILDER_REF, fake_builder, raising=False)
    op04 = _op04()

    assert called["value"] is False
    assert op04["existing_dhr_op05_builder_called_here"] is False
    assert op04["dhr_op05_call_allowed_here"] is False
    assert dhb.assert_p7_r54_ahr_post_pcm_dhb_op04_dhr_op05_manual_handoff_envelope_without_call_contract(op04) is True


@pytest.mark.parametrize("lane_ref", dhb.P7_R54_AHR_POST_PCM_DHB_ALLOWED_NON_DHR_LANE_REFS)
def test_dhb_op04_preserves_non_dhr_lane_without_handoff_envelope(lane_ref: str) -> None:
    op04 = _op04(selected_pnt_lane_ref=lane_ref, next_design_document_allowed=False)

    assert dhb.assert_p7_r54_ahr_post_pcm_dhb_op04_dhr_op05_manual_handoff_envelope_without_call_contract(op04) is True
    assert op04["dhb_op04_status_ref"] == dhb.P7_R54_AHR_POST_PCM_DHB_OP04_ALLOWED_STATUS_REFS[1]
    assert op04["dhr_op05_lane_confirmed"] is False
    assert op04["dhr_op05_manual_handoff_envelope_materialized"] is False
    assert op04["dhr_op05_handoff_envelope_ready"] is False
    assert op04["dhr_op05_preflight_reentry_candidate_allowed"] is False
    assert op04["preserved_non_dhr_lane_ref"] == lane_ref
    assert op04["preserved_pcm_route_without_execution"] is True
    assert op04["next_required_step"] == dhb.P7_R54_AHR_POST_PCM_DHB_NEXT_STEP_FOLLOW_PCM_R11_LANE_SPECIFIC_DECISION_TABLE_OUTSIDE_DHB_REF


def test_dhb_op04_repairs_when_op03_material_is_missing() -> None:
    op04 = dhb.build_p7_r54_ahr_post_pcm_dhb_op04_dhr_op05_manual_handoff_envelope_without_call(None)

    assert dhb.assert_p7_r54_ahr_post_pcm_dhb_op04_dhr_op05_manual_handoff_envelope_without_call_contract(op04) is True
    assert op04["dhb_op04_status_ref"] == dhb.P7_R54_AHR_POST_PCM_DHB_OP04_ALLOWED_STATUS_REFS[2]
    assert op04["dhb_op04_repair_required"] is True
    assert op04["dhr_op05_manual_handoff_envelope_materialized"] is False
    assert op04["next_required_step"] == dhb.P7_R54_AHR_POST_PCM_DHB_NEXT_STEP_REPAIR_DHR_OP05_HANDOFF_ENVELOPE_INPUTS_REF


@pytest.mark.parametrize(
    ("mutation_key", "expected_path_fragment"),
    [
        ("dhr_op05_called_here", "dhr_op05_called_here"),
        ("release_allowed", "release_allowed"),
        ("api_changed", "api_changed"),
    ],
)
def test_dhb_op04_blocks_dhr_call_release_or_no_touch_claim_from_input(
    mutation_key: str,
    expected_path_fragment: str,
) -> None:
    op03 = _op03()
    mutated = deepcopy(op03)
    mutated[mutation_key] = True
    op04 = dhb.build_p7_r54_ahr_post_pcm_dhb_op04_dhr_op05_manual_handoff_envelope_without_call(mutated)

    assert dhb.assert_p7_r54_ahr_post_pcm_dhb_op04_dhr_op05_manual_handoff_envelope_without_call_contract(op04) is True
    assert op04["dhb_op04_status_ref"] == dhb.P7_R54_AHR_POST_PCM_DHB_OP04_ALLOWED_STATUS_REFS[3]
    assert op04["dhb_op04_bodyfree_leak_promotion_or_autorun_blocked"] is True
    assert op04["dhr_op05_manual_handoff_envelope_materialized"] is False
    combined_paths = (
        tuple(op04["op04_input_forbidden_payload_key_path_refs"])
        + tuple(op04["op04_input_body_like_value_path_refs"])
        + tuple(op04["op04_input_promotion_claim_refs"])
        + tuple(op04["op04_input_no_touch_mutation_path_refs"])
    )
    assert any(expected_path_fragment in path for path in combined_paths)


def test_dhb_op04_assert_rejects_builder_called_promotion_mutation() -> None:
    op04 = _op04()
    mutated = deepcopy(op04)
    mutated["existing_dhr_op05_builder_called_here"] = True

    with pytest.raises(ValueError):
        dhb.assert_p7_r54_ahr_post_pcm_dhb_op04_dhr_op05_manual_handoff_envelope_without_call_contract(mutated)


def test_dhb_op05_records_existing_dhr_op05_compatibility_refs_without_generating_result() -> None:
    op05 = _op05()

    assert dhb.assert_p7_r54_ahr_post_pcm_dhb_op05_existing_dhr_op05_compatibility_crosswalk_without_call_contract(op05) is True
    assert op05["operation_step_ref"] == dhb.P7_R54_AHR_POST_PCM_DHB_OP05_STEP_REF
    assert op05["dhb_op05_status_ref"] == dhb.P7_R54_AHR_POST_PCM_DHB_OP05_ALLOWED_STATUS_REFS[0]
    assert op05["dhr_op05_compatibility_crosswalk_recorded"] is True
    assert tuple(op05["dhr_op05_compatibility_crosswalk_refs"]) == dhb.P7_R54_AHR_POST_PCM_DHB_EXISTING_DHR_OP05_COMPATIBILITY_CROSSWALK_REFS
    assert tuple(op05["existing_dhr_op05_compatibility_status_refs"]) == dhb.P7_R54_AHR_POST_PCM_DHB_EXISTING_DHR_OP05_COMPATIBILITY_STATUS_REFS
    assert op05["existing_dhr_op05_status_refs_are_compatibility_refs_only"] is True
    assert op05["existing_dhr_op05_status_generated_here"] is False
    assert op05["existing_dhr_op05_clear_status_generated_here"] is False
    assert op05["dhr_op05_result_generated_here"] is False
    assert op05["dhr_op05_preflight_scan_executed_here"] is False
    assert op05["dhr_op05_builder_input_materialized_here"] is False
    assert op05["next_required_step"] == dhb.P7_R54_AHR_POST_PCM_DHB_OP06_STEP_REF
    assert tuple(op05["implemented_steps"]) == dhb.P7_R54_AHR_POST_PCM_DHB_OP05_IMPLEMENTED_STEPS
    assert tuple(op05["not_yet_implemented_steps"]) == dhb.P7_R54_AHR_POST_PCM_DHB_OP05_NOT_YET_IMPLEMENTED_STEPS


def test_dhb_op05_does_not_call_existing_dhr_builder_even_when_callable_is_present(monkeypatch: pytest.MonkeyPatch) -> None:
    called = {"value": False}

    def fake_builder(*args: object, **kwargs: object) -> dict[str, object]:
        called["value"] = True
        return {"unexpected": True}

    monkeypatch.setattr(dhb, dhb.P7_R54_AHR_POST_PCM_DHB_EXISTING_DHR_OP05_BUILDER_REF, fake_builder, raising=False)
    op05 = _op05()

    assert called["value"] is False
    assert op05["existing_dhr_op05_builder_called_here"] is False
    assert op05["dhr_op05_preflight_scan_executed_here"] is False
    assert dhb.assert_p7_r54_ahr_post_pcm_dhb_op05_existing_dhr_op05_compatibility_crosswalk_without_call_contract(op05) is True


def test_dhb_op05_repairs_when_op04_handoff_envelope_is_missing() -> None:
    op05 = dhb.build_p7_r54_ahr_post_pcm_dhb_op05_existing_dhr_op05_compatibility_crosswalk_without_call(None)

    assert dhb.assert_p7_r54_ahr_post_pcm_dhb_op05_existing_dhr_op05_compatibility_crosswalk_without_call_contract(op05) is True
    assert op05["dhb_op05_status_ref"] == dhb.P7_R54_AHR_POST_PCM_DHB_OP05_ALLOWED_STATUS_REFS[1]
    assert op05["dhb_op05_compatibility_repair_required"] is True
    assert op05["dhr_op05_compatibility_crosswalk_recorded"] is False
    assert op05["next_required_step"] == dhb.P7_R54_AHR_POST_PCM_DHB_NEXT_STEP_REPAIR_DHR_OP05_COMPATIBILITY_CROSSWALK_REF


def test_dhb_op05_repairs_non_dhr_op04_without_turning_it_into_dhr_crosswalk() -> None:
    op04 = _op04(
        selected_pnt_lane_ref=dhb.P7_R54_AHR_POST_PCM_DHB_ALLOWED_NON_DHR_LANE_REFS[0],
        next_design_document_allowed=False,
    )
    op05 = dhb.build_p7_r54_ahr_post_pcm_dhb_op05_existing_dhr_op05_compatibility_crosswalk_without_call(op04)

    assert dhb.assert_p7_r54_ahr_post_pcm_dhb_op05_existing_dhr_op05_compatibility_crosswalk_without_call_contract(op05) is True
    assert op05["dhb_op05_status_ref"] == dhb.P7_R54_AHR_POST_PCM_DHB_OP05_ALLOWED_STATUS_REFS[1]
    assert op05["op04_non_dhr_no_handoff_envelope"] is True
    assert op05["dhr_op05_compatibility_crosswalk_recorded"] is False
    assert op05["dhr_op05_manual_handoff_envelope_ready"] is False


def test_dhb_op05_blocks_fake_dhr_op05_clear_status_in_input() -> None:
    op04 = _op04()
    mutated = deepcopy(op04)
    mutated["dhr_op05_preflight_status_ref"] = "DHR_PREFLIGHT_SCAN_CLEAR_BODYFREE"
    op05 = dhb.build_p7_r54_ahr_post_pcm_dhb_op05_existing_dhr_op05_compatibility_crosswalk_without_call(mutated)

    assert dhb.assert_p7_r54_ahr_post_pcm_dhb_op05_existing_dhr_op05_compatibility_crosswalk_without_call_contract(op05) is True
    assert op05["dhb_op05_status_ref"] == dhb.P7_R54_AHR_POST_PCM_DHB_OP05_ALLOWED_STATUS_REFS[2]
    assert op05["dhb_op05_compatibility_blocked_promotion_or_autorun"] is True
    assert op05["dhr_op05_compatibility_crosswalk_recorded"] is False
    assert op05["dhr_op05_result_generated_here"] is False
    assert any("dhr_op05_preflight_status_ref" in path for path in op05["op05_input_fake_dhr_op05_result_claim_path_refs"])


@pytest.mark.parametrize(
    ("mutation_key", "expected_path_fragment"),
    [
        ("dmd_execution_started_here", "dmd_execution_started_here"),
        ("r52_actual_execution_started_here", "r52_actual_execution_started_here"),
        ("release_allowed", "release_allowed"),
    ],
)
def test_dhb_op05_blocks_dmd_r52_or_release_claim_from_input(
    mutation_key: str,
    expected_path_fragment: str,
) -> None:
    op04 = _op04()
    mutated = deepcopy(op04)
    mutated[mutation_key] = True
    op05 = dhb.build_p7_r54_ahr_post_pcm_dhb_op05_existing_dhr_op05_compatibility_crosswalk_without_call(mutated)

    assert dhb.assert_p7_r54_ahr_post_pcm_dhb_op05_existing_dhr_op05_compatibility_crosswalk_without_call_contract(op05) is True
    assert op05["dhb_op05_status_ref"] == dhb.P7_R54_AHR_POST_PCM_DHB_OP05_ALLOWED_STATUS_REFS[2]
    assert op05["dhb_op05_compatibility_blocked_promotion_or_autorun"] is True
    combined_paths = (
        tuple(op05["op05_input_promotion_claim_refs"])
        + tuple(op05["op05_input_no_touch_mutation_path_refs"])
        + tuple(op05["op05_input_fake_dhr_op05_result_claim_path_refs"])
    )
    assert any(expected_path_fragment in path for path in combined_paths)


@pytest.mark.parametrize("key", _DHB_OP04_FALSE_CLAIM_KEYS)
def test_dhb_op04_keeps_forbidden_claims_false_in_output(key: str) -> None:
    op04 = _op04()

    assert op04[key] is False, key
    assert dhb.assert_p7_r54_ahr_post_pcm_dhb_op04_dhr_op05_manual_handoff_envelope_without_call_contract(op04) is True


@pytest.mark.parametrize("key", _DHB_OP05_FALSE_CLAIM_KEYS)
def test_dhb_op05_keeps_forbidden_claims_false_in_output(key: str) -> None:
    op05 = _op05()

    assert op05[key] is False, key
    assert dhb.assert_p7_r54_ahr_post_pcm_dhb_op05_existing_dhr_op05_compatibility_crosswalk_without_call_contract(op05) is True


def test_dhb_op05_assert_rejects_output_promotion_mutation() -> None:
    op05 = _op05()
    mutated = deepcopy(op05)
    mutated["dhr_op05_preflight_scan_executed_here"] = True

    with pytest.raises(ValueError):
        dhb.assert_p7_r54_ahr_post_pcm_dhb_op05_existing_dhr_op05_compatibility_crosswalk_without_call_contract(mutated)
