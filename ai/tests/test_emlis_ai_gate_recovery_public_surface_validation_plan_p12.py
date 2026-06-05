# -*- coding: utf-8 -*-
from __future__ import annotations

import json

import pytest

from emlis_ai_gate_recovery_public_constants import (
    BLOCKER_GATE_RECOVERY_DIAGNOSTIC_SURFACE_PROMOTED_TO_PUBLIC,
    BLOCKER_GATE_RECOVERY_MATERIAL_SURFACE_PUBLIC_LEAK,
    BLOCKER_POST_FINAL_GATE_RECOVERY_MATERIAL_SURFACE_PUBLIC_LEAK,
    CANDIDATE_SOURCE_KIND_GATE_RECOVERY_MATERIAL_SURFACE,
    CANDIDATE_SOURCE_KIND_LOW_INFORMATION_OBSERVATION_COMPOSER,
    PUBLIC_SURFACE_ROLE_DIAGNOSTIC_RECOVERY,
    PUBLIC_SURFACE_ROLE_PUBLIC_OBSERVATION,
)
from emlis_ai_gate_recovery_public_surface_validation_plan import (
    BLOCKER_P12_ACCEPTANCE_CRITERION_NOT_MET,
    BLOCKER_P12_CONTRACT_RELAXATION_DETECTED,
    BLOCKER_P12_RELEASE_FLAG_DETECTED,
    BLOCKER_P12_SOURCE_TEXT_PAYLOAD_DETECTED,
    BLOCKER_P12_VALIDATION_EXECUTION_REQUIRED,
    GATE_RECOVERY_PUBLIC_SURFACE_P12_VALIDATION_PHASE,
    GATE_RECOVERY_PUBLIC_SURFACE_P12_VALIDATION_SCHEMA_VERSION,
    VALIDATION_STATUS_PASSED,
    assert_gate_recovery_public_surface_p12_validation_plan_meta_only,
    build_gate_recovery_public_surface_p12_real_device_check_results_stub,
    build_gate_recovery_public_surface_p12_validation_plan,
    build_gate_recovery_public_surface_p12_validation_results_stub,
    dump_gate_recovery_public_surface_p12_validation_plan,
)

SECRET_INPUT = "P12_SECRET_RAW_INPUT_SHOULD_NOT_SURVIVE"
SECRET_COMMENT = "P12_SECRET_COMMENT_SHOULD_NOT_SURVIVE"


def _dump(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def _frontend_results(status: str = VALIDATION_STATUS_PASSED) -> dict[str, str]:
    return {"p10_rn_contract_regression": status}


def _green_measurement_run() -> dict[str, object]:
    return {
        "run_id": "p12_green_surface_origin_run",
        "event_count": 1,
        "blockers": [],
        "machine_metrics": {
            "event_count": 1,
            "display_reach_rate": 1.0,
            "surface_origin_event_count": 1,
            "public_display_reached_via_gate_recovery_material_surface_count": 0,
            "public_display_reached_via_post_final_gate_recovery_material_surface_count": 0,
            "public_display_reached_via_diagnostic_recovery_surface_count": 0,
        },
        "surface_origin_summary": {
            "event_count": 1,
            "surface_origin_event_count": 1,
            "gate_recovery_material_surface_event_count": 0,
            "post_final_gate_recovery_material_surface_event_count": 0,
            "public_diagnostic_recovery_surface_event_count": 0,
        },
        "measurement_events": [
            {
                "row_id": "p12_allowed_low_info_row",
                "family": "daily_positive",
                "public_display_reached": True,
                "blockers": [],
                "surface_origin": {
                    "candidate_source_kind": CANDIDATE_SOURCE_KIND_LOW_INFORMATION_OBSERVATION_COMPOSER,
                    "public_surface_role": PUBLIC_SURFACE_ROLE_PUBLIC_OBSERVATION,
                    "public_display_allowed_by_boundary": True,
                    "gate_recovery_material_surface_detected": False,
                    "post_final_gate_recovery_material_surface_detected": False,
                    "internal_policy_sentence_leak_risk": False,
                    "template_meta_false_negative_risk": False,
                    "raw_input_included": False,
                    "comment_text_body_included": False,
                },
            }
        ],
        "contract_assertions": {
            "api_route_changed": False,
            "response_shape_changed": False,
            "public_response_key_added": False,
            "db_physical_name_changed": False,
            "rn_visible_contract_changed": False,
            "display_gate_relaxed": False,
            "grounding_gate_relaxed": False,
            "template_gate_relaxed": False,
            "raw_input_included": False,
            "comment_text_body_included": False,
        },
        "product_gate_ready": False,
        "public_release_applied": False,
    }


def _leaky_measurement_run() -> dict[str, object]:
    return {
        "run_id": "p12_leaky_gate_recovery_run",
        "event_count": 2,
        "blockers": [
            BLOCKER_GATE_RECOVERY_MATERIAL_SURFACE_PUBLIC_LEAK,
            BLOCKER_POST_FINAL_GATE_RECOVERY_MATERIAL_SURFACE_PUBLIC_LEAK,
            BLOCKER_GATE_RECOVERY_DIAGNOSTIC_SURFACE_PROMOTED_TO_PUBLIC,
        ],
        "machine_metrics": {
            "event_count": 2,
            "display_reach_rate": 1.0,
            "surface_origin_event_count": 2,
            "public_display_reached_via_gate_recovery_material_surface_count": 2,
            "public_display_reached_via_post_final_gate_recovery_material_surface_count": 1,
            "public_display_reached_via_diagnostic_recovery_surface_count": 2,
        },
        "surface_origin_summary": {
            "event_count": 2,
            "surface_origin_event_count": 2,
            "gate_recovery_material_surface_event_count": 2,
            "post_final_gate_recovery_material_surface_event_count": 1,
            "public_diagnostic_recovery_surface_event_count": 2,
        },
        "measurement_events": [
            {
                "row_id": "p12_leak_row_1",
                "family": "relationship_boundary",
                "public_display_reached": True,
                "blockers": [BLOCKER_GATE_RECOVERY_MATERIAL_SURFACE_PUBLIC_LEAK],
                "surface_origin": {
                    "candidate_source_kind": CANDIDATE_SOURCE_KIND_GATE_RECOVERY_MATERIAL_SURFACE,
                    "public_surface_role": PUBLIC_SURFACE_ROLE_DIAGNOSTIC_RECOVERY,
                    "public_display_allowed_by_boundary": False,
                    "gate_recovery_material_surface_detected": True,
                    "post_final_gate_recovery_material_surface_detected": False,
                    "raw_input_included": False,
                    "comment_text_body_included": False,
                },
            },
            {
                "row_id": "p12_leak_row_2",
                "family": "mixed_emotion",
                "public_display_reached": True,
                "blockers": [BLOCKER_POST_FINAL_GATE_RECOVERY_MATERIAL_SURFACE_PUBLIC_LEAK],
                "surface_origin": {
                    "candidate_source_kind": CANDIDATE_SOURCE_KIND_GATE_RECOVERY_MATERIAL_SURFACE,
                    "public_surface_role": PUBLIC_SURFACE_ROLE_DIAGNOSTIC_RECOVERY,
                    "public_display_allowed_by_boundary": False,
                    "gate_recovery_material_surface_detected": True,
                    "post_final_gate_recovery_material_surface_detected": True,
                    "raw_input_included": False,
                    "comment_text_body_included": False,
                },
            },
        ],
        "product_gate_ready": False,
        "public_release_applied": False,
    }


def test_p12_validation_plan_materializes_required_backend_frontend_and_manual_checks() -> None:
    plan = build_gate_recovery_public_surface_p12_validation_plan(run_id="p12_pending")

    assert plan["schema_version"] == GATE_RECOVERY_PUBLIC_SURFACE_P12_VALIDATION_SCHEMA_VERSION
    assert plan["phase"] == GATE_RECOVERY_PUBLIC_SURFACE_P12_VALIDATION_PHASE
    assert plan["validation_plan_ready"] is True
    assert plan["validation_ready"] is False
    assert BLOCKER_P12_VALIDATION_EXECUTION_REQUIRED in plan["validation_blockers"]
    assert len(plan["validation_items"]) == 11
    assert len(plan["manual_validation_items"]) == 5
    assert plan["validation_items"][0]["validation_item_id"] == "p0_p2_public_surface_boundary_contract"
    assert plan["validation_items"][8]["validation_item_id"] == "p10_rn_contract_regression"
    assert plan["validation_items"][9]["validation_item_id"] == "p11_real_device_regression_fixture_handling"
    assert "npm run test:rn-screens" in plan["validation_items"][8]["command"]
    assert plan["expected_runtime_policy"]["gate_recovery_material_surface_public_candidate_allowed"] is False
    assert plan["expected_runtime_policy"]["post_final_direct_material_surface_promotion_allowed"] is False
    assert plan["product_gate_ready"] is False
    assert plan["public_release_applied"] is False
    assert_gate_recovery_public_surface_p12_validation_plan_meta_only(plan)


def test_p12_validation_plan_becomes_ready_only_after_results_surface_origin_and_manual_checks_are_green() -> None:
    plan = build_gate_recovery_public_surface_p12_validation_plan(
        run_id="p12_green",
        measurement_run=_green_measurement_run(),
        validation_results=build_gate_recovery_public_surface_p12_validation_results_stub(),
        frontend_validation_results=_frontend_results(),
        real_device_check_results=build_gate_recovery_public_surface_p12_real_device_check_results_stub(),
    )

    assert plan["validation_ready"] is True
    assert plan["validation_passed"] is True
    assert plan["release_allowed_by_validation_plan"] is True
    assert plan["validation_blockers"] == []
    assert plan["all_required_validation_passed"] is True
    assert plan["all_acceptance_criteria_passed"] is True
    assert all(row["status"] == VALIDATION_STATUS_PASSED for row in plan["validation_steps"])
    assert all(row["passed"] is True for row in plan["acceptance_criteria"])
    assert plan["product_gate_ready"] is False
    assert plan["public_release_applied"] is False
    assert_gate_recovery_public_surface_p12_validation_plan_meta_only(plan)


def test_p12_validation_plan_blocks_gate_recovery_public_surface_leak_even_if_command_results_pass() -> None:
    plan = build_gate_recovery_public_surface_p12_validation_plan(
        run_id="p12_leak",
        measurement_run=_leaky_measurement_run(),
        validation_results=build_gate_recovery_public_surface_p12_validation_results_stub(),
        frontend_validation_results=_frontend_results(),
        real_device_check_results=build_gate_recovery_public_surface_p12_real_device_check_results_stub(),
    )

    assert plan["validation_ready"] is False
    assert BLOCKER_P12_ACCEPTANCE_CRITERION_NOT_MET in plan["validation_blockers"]
    assert BLOCKER_GATE_RECOVERY_MATERIAL_SURFACE_PUBLIC_LEAK in plan["validation_blockers"]
    assert BLOCKER_POST_FINAL_GATE_RECOVERY_MATERIAL_SURFACE_PUBLIC_LEAK in plan["validation_blockers"]
    assert BLOCKER_GATE_RECOVERY_DIAGNOSTIC_SURFACE_PROMOTED_TO_PUBLIC in plan["validation_blockers"]
    assert plan["surface_origin_observed_counts"]["public_display_reached_via_gate_recovery_material_surface_count"] == 2
    assert plan["surface_origin_observed_counts"]["public_display_reached_via_post_final_gate_recovery_material_surface_count"] == 1
    assert plan["surface_origin_observed_counts"]["public_display_reached_via_diagnostic_recovery_surface_count"] == 2
    assert any(
        row["criterion_id"] == "public_display_via_gate_recovery_material_surface_zero"
        and row["passed"] is False
        for row in plan["acceptance_criteria"]
    )
    assert plan["product_gate_ready"] is False
    assert plan["public_release_applied"] is False


def test_p12_validation_plan_detects_source_payload_without_serializing_secret() -> None:
    unsafe_run = dict(_green_measurement_run())
    unsafe_run["comment_text"] = SECRET_COMMENT
    unsafe_run["raw_input"] = SECRET_INPUT
    plan = build_gate_recovery_public_surface_p12_validation_plan(
        run_id="p12_source_payload",
        measurement_run=unsafe_run,
        validation_results=build_gate_recovery_public_surface_p12_validation_results_stub(),
        frontend_validation_results=_frontend_results(),
        real_device_check_results=build_gate_recovery_public_surface_p12_real_device_check_results_stub(),
    )

    assert plan["source_text_payload_detected"] is True
    assert BLOCKER_P12_SOURCE_TEXT_PAYLOAD_DETECTED in plan["validation_blockers"]
    dumped = dump_gate_recovery_public_surface_p12_validation_plan(plan)
    assert SECRET_INPUT not in dumped
    assert SECRET_COMMENT not in dumped
    assert '"comment_text"' not in dumped
    assert '"raw_input"' not in dumped


def test_p12_validation_plan_rejects_contract_relaxation_release_flags_and_body_keys() -> None:
    base = build_gate_recovery_public_surface_p12_validation_plan(run_id="p12_assert")

    unsafe_body = dict(base)
    unsafe_body["comment_text"] = SECRET_COMMENT
    with pytest.raises(ValueError):
        assert_gate_recovery_public_surface_p12_validation_plan_meta_only(unsafe_body)

    unsafe_contract = dict(base)
    unsafe_contract["public_response_key_added"] = True
    with pytest.raises(ValueError):
        assert_gate_recovery_public_surface_p12_validation_plan_meta_only(unsafe_contract)

    unsafe_release = dict(base)
    unsafe_release["product_gate_ready"] = True
    with pytest.raises(ValueError):
        assert_gate_recovery_public_surface_p12_validation_plan_meta_only(unsafe_release)

    plan = build_gate_recovery_public_surface_p12_validation_plan(
        run_id="p12_source_contract_flags",
        measurement_run={"run_id": "p12_source_contract_flags", "display_gate_relaxed": True},
        validation_results=build_gate_recovery_public_surface_p12_validation_results_stub(),
        frontend_validation_results=_frontend_results(),
        real_device_check_results=build_gate_recovery_public_surface_p12_real_device_check_results_stub(),
    )
    assert BLOCKER_P12_CONTRACT_RELAXATION_DETECTED in plan["validation_blockers"]

    plan_with_release_source = build_gate_recovery_public_surface_p12_validation_plan(
        run_id="p12_source_release_flags",
        measurement_run={"run_id": "p12_source_release_flags", "public_release_applied": True},
        validation_results=build_gate_recovery_public_surface_p12_validation_results_stub(),
        frontend_validation_results=_frontend_results(),
        real_device_check_results=build_gate_recovery_public_surface_p12_real_device_check_results_stub(),
    )
    assert BLOCKER_P12_RELEASE_FLAG_DETECTED in plan_with_release_source["validation_blockers"]


def test_p12_dump_is_meta_only() -> None:
    plan = build_gate_recovery_public_surface_p12_validation_plan(
        run_id="p12_dump",
        measurement_run=_green_measurement_run(),
        validation_results=build_gate_recovery_public_surface_p12_validation_results_stub(),
        frontend_validation_results=_frontend_results(),
        real_device_check_results=build_gate_recovery_public_surface_p12_real_device_check_results_stub(),
    )
    dumped = dump_gate_recovery_public_surface_p12_validation_plan(plan)

    assert _dump(plan)
    assert "P12_SECRET" not in dumped
    assert '"raw_input"' not in dumped
    assert '"comment_text"' not in dumped
    assert '"candidate_body"' not in dumped
