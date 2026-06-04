# -*- coding: utf-8 -*-
from __future__ import annotations

import json

import pytest

from emlis_ai_product_quality_measurement_runner import (
    dump_product_quality_measurement_run,
    run_product_quality_measurement,
)
from emlis_ai_product_quality_validation_plan import (
    BLOCKER_VALIDATION_EXECUTION_REQUIRED,
    PRODUCT_QUALITY_VALIDATION_PLAN_PHASE,
    PRODUCT_QUALITY_VALIDATION_PLAN_SCHEMA_VERSION,
    VALIDATION_STATUS_PASSED,
    assert_product_quality_validation_plan_meta_only,
    build_product_quality_validation_plan,
    build_product_quality_validation_results_stub,
    dump_product_quality_validation_plan,
)

SECRET_INPUT = "PHASE8_SECRET_RAW_INPUT_SHOULD_NOT_SURVIVE"
SECRET_COMMENT = "PHASE8_SECRET_COMMENT_SHOULD_NOT_SURVIVE"


def _dump(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def _green_measurement_run() -> dict[str, object]:
    return {
        "run_id": "pq_phase8_green",
        "run_status": "completed",
        "event_count": 12,
        "family_counts": {"daily_unpleasant": 1},
        "required_families": ["daily_unpleasant"],
        "missing_required_families": [],
        "summary_metrics": {
            "display_reach_rate": 1.0,
            "binding_pass_rate": 1.0,
            "reason_coverage_rate": 1.0,
            "runtime_surface_blind_qa_coverage_rate": 1.0,
            "runtime_surface_blind_qa_read_feeling_score": 1.0,
            "user_label_connection_qa_coverage_rate": 1.0,
            "user_label_connection_quality_score": 1.0,
            "red_review_count": 0,
            "repair_required_row_count": 0,
            "five_consecutive_product_pass": True,
            "ten_consecutive_product_pass": True,
            "family_cross_surface_repetition_detected": False,
            "unsafe_insight_surface_detected": False,
        },
        "contract_assertions": {
            "api_route_changed": False,
            "response_shape_changed": False,
            "public_response_key_added": False,
            "db_physical_name_changed": False,
            "rn_visible_contract_changed": False,
            "rn_visible_title_changed": False,
            "display_gate_relaxed": False,
            "grounding_gate_relaxed": False,
            "template_gate_relaxed": False,
            "raw_input_included": False,
            "raw_text_included": False,
            "comment_text_body_included": False,
            "candidate_body_included": False,
            "surface_body_included": False,
        },
        "product_gate_ready": False,
        "public_release_applied": False,
    }


def _green_release_decision() -> dict[str, object]:
    return {
        "run_id": "pq_phase8_green",
        "release_allowed": True,
        "release_stage": "release_candidate",
        "release_blockers": [],
        "required_followup_fixes": [],
        "product_gate_ready": False,
        "public_release_applied": False,
    }


def test_phase8_validation_plan_materializes_required_order_as_pending_internal_material() -> None:
    plan = build_product_quality_validation_plan(run_id="pq_phase8_pending")

    assert plan["schema_version"] == PRODUCT_QUALITY_VALIDATION_PLAN_SCHEMA_VERSION
    assert plan["phase"] == PRODUCT_QUALITY_VALIDATION_PLAN_PHASE
    assert plan["validation_plan_ready"] is True
    assert plan["validation_ready"] is False
    assert plan["validation_execution_required"] is True
    assert BLOCKER_VALIDATION_EXECUTION_REQUIRED in plan["validation_blockers"]
    assert len(plan["validation_items"]) == 10
    assert [row["execution_order"] for row in plan["validation_items"]] == list(range(1, 11))
    assert plan["validation_items"][0]["validation_item_id"] == "public_boundary_and_rn_contract_tests"
    assert plan["validation_items"][-1]["validation_item_id"] == "emotion_submit_public_boundary_e2e_tests"
    assert plan["regression_policy"]["abcd_fixture_is_regression_only"] is True
    assert plan["regression_policy"]["runtime_fixture_branch_allowed"] is False
    assert plan["product_gate_ready"] is False
    assert plan["public_release_applied"] is False
    assert_product_quality_validation_plan_meta_only(plan)


def test_phase8_validation_plan_can_become_ready_only_with_validation_results_targets_and_release_candidate() -> None:
    validation_results = build_product_quality_validation_results_stub(VALIDATION_STATUS_PASSED)
    plan = build_product_quality_validation_plan(
        run_id="pq_phase8_green",
        measurement_run=_green_measurement_run(),
        release_decision=_green_release_decision(),
        validation_results=validation_results,
    )

    assert plan["validation_ready"] is True
    assert plan["validation_passed"] is True
    assert plan["release_allowed_by_validation_plan"] is True
    assert plan["validation_blockers"] == []
    assert plan["all_required_validation_passed"] is True
    assert plan["all_acceptance_criteria_passed"] is True
    assert all(row["status"] == VALIDATION_STATUS_PASSED for row in plan["validation_items"])
    assert all(row["passed"] is True for row in plan["acceptance_criteria"])
    assert_product_quality_validation_plan_meta_only(plan)


def test_phase8_validation_plan_rejects_body_payload_contract_relaxation_and_release_flags() -> None:
    base = build_product_quality_validation_plan(run_id="pq_phase8_assert")

    unsafe_payload = dict(base)
    unsafe_payload["comment_text"] = SECRET_COMMENT
    with pytest.raises(ValueError):
        assert_product_quality_validation_plan_meta_only(unsafe_payload)

    unsafe_contract = dict(base)
    unsafe_contract["public_response_key_added"] = True
    with pytest.raises(ValueError):
        assert_product_quality_validation_plan_meta_only(unsafe_contract)

    unsafe_release = dict(base)
    unsafe_release["product_gate_ready"] = True
    with pytest.raises(ValueError):
        assert_product_quality_validation_plan_meta_only(unsafe_release)


def test_phase8_validation_plan_detects_source_material_leaks_without_serializing_secret() -> None:
    plan = build_product_quality_validation_plan(
        run_id="pq_phase8_source_leak",
        measurement_run={
            "run_id": "pq_phase8_source_leak",
            "summary_metrics": {"display_reach_rate": 1.0},
            "comment_text": SECRET_COMMENT,
            "product_gate_ready": False,
            "public_release_applied": False,
        },
        release_decision={"release_allowed": False, "release_stage": "not_ready", "release_blockers": []},
    )

    assert plan["source_text_payload_detected"] is True
    assert "phase8_source_text_payload_detected" in plan["validation_blockers"]
    dumped = dump_product_quality_validation_plan(plan)
    assert SECRET_INPUT not in dumped
    # The source secret is not copied into the plan; only a detector flag remains.
    assert SECRET_COMMENT not in dumped


def test_phase8_measurement_runner_connects_validation_plan_without_changing_public_contract() -> None:
    run = run_product_quality_measurement(env={}, enable_composer=False)

    assert run["validation_plan"]["schema_version"] == PRODUCT_QUALITY_VALIDATION_PLAN_SCHEMA_VERSION
    assert run["phase8_validation_plan_ready"] is True
    assert run["phase8_validation_status"] == "blocked"
    assert run["phase8_validation_execution_required"] is True
    assert run["phase8_validation_passed"] is False
    assert run["phase8_release_allowed_by_validation_plan"] is False
    assert run["phase8_public_response_changed"] is False
    assert run["phase8_rn_contract_changed"] is False
    assert run["phase8_db_schema_changed"] is False
    assert len(run["validation_execution_order"]) == 10
    assert run["product_gate_ready"] is False
    assert run["public_release_applied"] is False
    dumped = dump_product_quality_measurement_run(run)
    assert '"comment_text":' not in dumped
    assert '"raw_input":' not in dumped
