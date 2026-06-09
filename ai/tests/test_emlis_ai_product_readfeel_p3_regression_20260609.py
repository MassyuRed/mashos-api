# -*- coding: utf-8 -*-
from __future__ import annotations

import json

import pytest

from emlis_ai_product_readfeel_p3_first_repair_design import (
    build_product_readfeel_p3_first_repair_design_20260609,
)
from emlis_ai_product_readfeel_p3_regression import (
    BASELINE_REGRESSION_REQUIRED_SUITE_IDS_20260609,
    DECISION_BLOCKED_NOT_EXECUTED,
    DECISION_BLOCKED_P2_RED,
    DECISION_BLOCKED_REQUIRED_FAILURE,
    DECISION_NO_RUNTIME_TARGET,
    DECISION_READY_FOR_FIRST_REPAIR,
    DECISION_YELLOW_TIMEOUT,
    PRODUCT_READFEEL_P3_REGRESSION_RESULT_VERSION_20260609,
    PRODUCT_READFEEL_P3_REGRESSION_STEP_20260609,
    PRODUCT_READFEEL_P3_REGRESSION_SUMMARY_VERSION_20260609,
    PRODUCT_READFEEL_P3_REGRESSION_VERSION_20260609,
    STATUS_FAILED,
    STATUS_PASSED,
    assert_product_readfeel_p3_regression_meta_only_20260609,
    build_product_readfeel_p3_regression_green_fixture_results_20260609,
    build_product_readfeel_p3_regression_plan_20260609,
    build_product_readfeel_p3_regression_result_20260609,
    dump_product_readfeel_p3_regression_public_summary_20260609,
)
from emlis_ai_product_readfeel_p3_verdict_split import (
    VERDICT_LAYER_P2_RED,
    VERDICT_LAYER_P3_REPAIR_REQUIRED,
)
from fixtures.emlis_ai_product_readfeel_p3_regression_20260609 import (
    build_product_readfeel_p3_regression_plan_from_first_repair_design_20260609,
    build_product_readfeel_p3_regression_result_from_first_repair_design_20260609,
    dump_product_readfeel_p3_regression_summary_from_first_repair_design_20260609,
)


def _first_repair_design_with_runtime_targets() -> dict[str, object]:
    return build_product_readfeel_p3_first_repair_design_20260609(
        repair_priority_items=[
            {
                "priority": 1,
                "blocker_id": "rich_input_low_information_overroute",
                "blocker_category": "readfeel_gap",
                "verdict_layer": VERDICT_LAYER_P3_REPAIR_REQUIRED,
                "case_count": 6,
                "families": ["daily_unpleasant", "mixed_emotion"],
                "sample_case_ids": ["p3-daily-unpleasant-001", "p3-mixed-emotion-002"],
                "reason_codes": ["rich_input_low_information_overroute", "input_core_missing"],
                "target_layers": ["input_material_bundle", "public_surface_requirement"],
            },
            {
                "priority": 2,
                "blocker_id": "generic_reception_surface",
                "blocker_category": "readfeel_gap",
                "verdict_layer": VERDICT_LAYER_P3_REPAIR_REQUIRED,
                "case_count": 4,
                "families": ["structure_question"],
                "sample_case_ids": ["p3-structure-question-003"],
                "reason_codes": ["generic_reception_surface", "family_temperature_flattened"],
                "target_layers": ["complete_surface_realizer", "ratio_policy"],
            },
        ],
        run_id="p3-8-runtime-design-source",
    )


def _first_repair_design_with_p2_red() -> dict[str, object]:
    return build_product_readfeel_p3_first_repair_design_20260609(
        repair_priority_items=[
            {
                "priority": 1,
                "blocker_id": "self_denial_identity_claim_risk",
                "blocker_category": "surface_breakage",
                "verdict_layer": VERDICT_LAYER_P2_RED,
                "case_count": 2,
                "families": ["self_denial"],
                "sample_case_ids": ["p3-self-denial-001"],
                "reason_codes": ["self_denial_identity_claim_risk"],
            }
        ],
        run_id="p3-8-p2-red-design-source",
    )


def test_p3_8_regression_plan_connects_p3_7_design_to_required_suites() -> None:
    design = _first_repair_design_with_runtime_targets()
    plan = build_product_readfeel_p3_regression_plan_20260609(
        first_repair_design=design,
        run_id="p3-8-plan",
        include_optional_suites=True,
    )
    summary = plan["summary"]
    suite_ids = {suite["suite_id"] for suite in plan["regression_suites"]}

    assert plan["schema_version"] == PRODUCT_READFEEL_P3_REGRESSION_VERSION_20260609
    assert plan["source_step"] == PRODUCT_READFEEL_P3_REGRESSION_STEP_20260609
    assert set(BASELINE_REGRESSION_REQUIRED_SUITE_IDS_20260609).issubset(suite_ids)
    assert "p3_grouped_chain_timeout_probe" in suite_ids
    assert summary["source_p3_7_runtime_repair_design_count"] == 2
    assert summary["p3_runtime_repair_can_start_from_design"] is True
    assert summary["p3_8_regression_plan_created"] is True
    assert summary["regression_must_precede_runtime_repair"] is True
    assert summary["comment_text_body_included"] is False
    assert summary["raw_input_included"] is False
    assert summary["raw_test_output_included"] is False
    assert plan["runtime_repair_applied"] is False
    assert plan["implementation_change_applied"] is False
    assert plan["product_gate_ready"] is False
    assert plan["public_release_applied"] is False
    assert_product_readfeel_p3_regression_meta_only_20260609(plan)


def test_p3_8_regression_result_all_required_green_allows_first_repair_implementation() -> None:
    design = _first_repair_design_with_runtime_targets()
    result = build_product_readfeel_p3_regression_result_20260609(
        first_repair_design=design,
        command_results=build_product_readfeel_p3_regression_green_fixture_results_20260609(),
        run_id="p3-8-green",
    )
    summary = result["summary"]

    assert result["schema_version"] == PRODUCT_READFEEL_P3_REGRESSION_VERSION_20260609
    assert all(row["schema_version"] == PRODUCT_READFEEL_P3_REGRESSION_RESULT_VERSION_20260609 for row in result["regression_result_rows"])
    assert summary["required_regression_green"] is True
    assert summary["p3_runtime_repair_can_start_after_regression"] is True
    assert summary["decision"] == DECISION_READY_FOR_FIRST_REPAIR
    assert summary["required_passed_count"] == len(BASELINE_REGRESSION_REQUIRED_SUITE_IDS_20260609)
    assert_product_readfeel_p3_regression_meta_only_20260609(result)


def test_p3_8_regression_optional_grouped_timeout_is_yellow_when_split_required_suites_are_green() -> None:
    design = _first_repair_design_with_runtime_targets()
    result = build_product_readfeel_p3_regression_result_20260609(
        first_repair_design=design,
        command_results=build_product_readfeel_p3_regression_green_fixture_results_20260609(
            include_optional_timeout=True
        ),
        run_id="p3-8-yellow-timeout",
    )
    summary = result["summary"]

    assert summary["required_regression_green"] is True
    assert summary["optional_timeout_yellow_present"] is True
    assert summary["optional_yellow_timeout_suite_ids"] == ["p3_grouped_chain_timeout_probe"]
    assert summary["p3_runtime_repair_can_start_after_regression"] is True
    assert summary["decision"] == DECISION_YELLOW_TIMEOUT
    assert_product_readfeel_p3_regression_meta_only_20260609(result)


def test_p3_8_regression_required_failure_blocks_first_repair_implementation() -> None:
    design = _first_repair_design_with_runtime_targets()
    rows = build_product_readfeel_p3_regression_green_fixture_results_20260609()
    rows[1] = {
        "suite_id": "backend_contract_display_split",
        "status": STATUS_FAILED,
        "passed_count": 5,
        "failed_count": 1,
        "failure_codes": ["backend_display_contract_failure"],
    }
    result = build_product_readfeel_p3_regression_result_20260609(
        first_repair_design=design,
        command_results=rows,
        run_id="p3-8-required-failure",
    )
    summary = result["summary"]

    assert summary["required_regression_green"] is False
    assert summary["required_failed_suite_ids"] == ["backend_contract_display_split"]
    assert summary["p3_runtime_repair_can_start_after_regression"] is False
    assert summary["decision"] == DECISION_BLOCKED_REQUIRED_FAILURE
    assert_product_readfeel_p3_regression_meta_only_20260609(result)


def test_p3_8_regression_missing_required_results_blocks_until_executed() -> None:
    design = _first_repair_design_with_runtime_targets()
    result = build_product_readfeel_p3_regression_result_20260609(
        first_repair_design=design,
        command_results=[
            {"suite_id": "rn_contract", "status": STATUS_PASSED, "passed_count": 36, "failed_count": 0}
        ],
        run_id="p3-8-not-executed",
    )
    summary = result["summary"]

    assert summary["required_regression_green"] is False
    assert "backend_contract_display_split" in summary["missing_required_suite_ids"]
    assert summary["p3_runtime_repair_can_start_after_regression"] is False
    assert summary["decision"] == DECISION_BLOCKED_NOT_EXECUTED
    assert_product_readfeel_p3_regression_meta_only_20260609(result)


def test_p3_8_regression_keeps_p2_red_ahead_of_p3_runtime_repair() -> None:
    design = _first_repair_design_with_p2_red()
    result = build_product_readfeel_p3_regression_result_20260609(
        first_repair_design=design,
        command_results=build_product_readfeel_p3_regression_green_fixture_results_20260609(),
        run_id="p3-8-p2-red",
    )
    summary = result["summary"]

    assert summary["p2_red_present"] is True
    assert summary["p2_red_blocks_p3_repair"] is True
    assert summary["required_regression_green"] is True
    assert summary["p3_runtime_repair_can_start_after_regression"] is False
    assert summary["decision"] == DECISION_BLOCKED_P2_RED
    assert_product_readfeel_p3_regression_meta_only_20260609(result)


def test_p3_8_fixture_connector_can_build_body_free_regression_summary() -> None:
    design = _first_repair_design_with_runtime_targets()
    plan = build_product_readfeel_p3_regression_plan_from_first_repair_design_20260609(
        first_repair_design=design,
        run_id="p3-8-fixture-plan",
    )
    result = build_product_readfeel_p3_regression_result_from_first_repair_design_20260609(
        regression_plan=plan,
        run_id="p3-8-fixture-result",
    )
    dumped = dump_product_readfeel_p3_regression_summary_from_first_repair_design_20260609(
        regression_plan=plan,
        command_results=build_product_readfeel_p3_regression_green_fixture_results_20260609(),
        run_id="p3-8-fixture-dump",
    )
    parsed = json.loads(dumped)

    assert plan["schema_version"] == PRODUCT_READFEEL_P3_REGRESSION_VERSION_20260609
    assert result["summary"]["decision"] == DECISION_READY_FOR_FIRST_REPAIR
    assert parsed["schema_version"] == PRODUCT_READFEEL_P3_REGRESSION_SUMMARY_VERSION_20260609
    assert "regression_suites" in parsed
    assert "regression_result_summary" in parsed
    assert "regression_result_rows" not in parsed
    assert "design_items" not in parsed
    assert "current_output_inventory\":" not in dumped
    assert "local review" not in dumped.lower()
    assert "Emlisです" not in dumped
    assert_product_readfeel_p3_regression_meta_only_20260609(parsed)


def test_p3_8_meta_only_guard_rejects_body_keys_raw_logs_and_contract_breaking_flags() -> None:
    with pytest.raises(ValueError):
        assert_product_readfeel_p3_regression_meta_only_20260609(
            {"schema_version": "unsafe", "comment_text": "actual display body must not enter P3-8"}
        )
    with pytest.raises(ValueError):
        assert_product_readfeel_p3_regression_meta_only_20260609(
            {"schema_version": "unsafe", "stdout": "raw pytest output must not be retained"}
        )
    with pytest.raises(ValueError):
        assert_product_readfeel_p3_regression_meta_only_20260609(
            {"schema_version": "unsafe", "gate_relaxed": True}
        )
    with pytest.raises(ValueError):
        assert_product_readfeel_p3_regression_meta_only_20260609(
            {"schema_version": "unsafe", "case_specific_runtime_branch": True}
        )
