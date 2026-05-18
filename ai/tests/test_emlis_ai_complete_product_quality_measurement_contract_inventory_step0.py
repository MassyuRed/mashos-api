from __future__ import annotations

import json

import pytest

from emlis_ai_complete_product_quality_measurement_contract_inventory import (
    PRODUCT_GATE_MEASUREMENT_CONTRACT_INVENTORY_VERSION,
    assert_product_gate_measurement_contract_inventory_meta_only,
    build_product_gate_measurement_contract_inventory,
    dump_product_gate_measurement_contract_inventory,
)


def test_step0_contract_inventory_fixes_measurement_scope_without_release_or_contract_changes() -> None:
    inventory = build_product_gate_measurement_contract_inventory()

    assert inventory["version"] == PRODUCT_GATE_MEASUREMENT_CONTRACT_INVENTORY_VERSION
    assert inventory["status"] == "fixed"
    assert inventory["measurement_connection_only"] is True
    assert "Step2: backend/frontend join semantics" in inventory["steps_in_scope"]
    assert "Step3: joined row -> scorecard event adapter" in inventory["steps_in_scope"]
    assert "Step4: measurement run builder" in inventory["steps_in_scope"]
    assert "Step5: coverage group aggregation" in inventory["steps_in_scope"]
    assert "Step6: Blind QA separation" in inventory["steps_in_scope"]
    assert "Step7: next action routing" in inventory["steps_in_scope"]
    assert "Step8: local tool output" in inventory["steps_in_scope"]
    assert "Step9: regression tests" in inventory["steps_in_scope"]
    assert "Step10: Exit Gate" in inventory["steps_in_scope"]
    assert inventory["scope"] == "Complete Composer ProductGate Measurement Step0-10"
    assert inventory["product_gate_achieved"] is False
    assert inventory["public_release_applied"] is False
    assert inventory["rn_visible_contract_change_allowed"] is False
    assert inventory["api_response_key_change_allowed"] is False
    assert inventory["db_physical_rename_allowed"] is False
    assert inventory["gate_relaxation_allowed"] is False
    assert inventory["regression_tests_ready"] is True
    assert inventory["step9_regression_tests_required"] is True
    assert inventory["step9_regression_tests_are_public_release"] is False
    assert inventory["regression_public_contract_checks_required"] is True
    assert inventory["regression_meta_only_checks_required"] is True
    assert inventory["regression_display_counting_checks_required"] is True
    assert inventory["regression_rn_contract_checks_required"] is True
    assert inventory["rn_runtime_files_modified_by_measurement"] is False
    assert inventory["exit_gate_ready"] is True
    assert inventory["step10_exit_gate_required"] is True
    assert inventory["step10_exit_gate_is_product_gate_achievement"] is False
    assert inventory["step10_exit_gate_public_release_applied"] is False
    assert inventory["exit_gate_required"] is True
    assert inventory["exit_gate_ready_requires_measurement_connection"] is True
    assert inventory["exit_gate_is_product_gate_achievement"] is False
    assert inventory["step10_exit_gate_is_public_release"] is False
    assert inventory["step10_fixture_regression_required"] is True
    assert set(inventory["step10_required_fixture_classes"]) == {
        "diagnostic_missing",
        "backend_rejected",
        "passed_hidden",
        "display_confirmed",
    }
    assert "diagnostic_compare_capture_and_join_semantics" in inventory["regression_test_targets"]
    assert "measurement_connection_scorecard_and_release_ladder" in inventory["regression_test_targets"]
    assert "local_tool_json_markdown_meta_only_output" in inventory["regression_test_targets"]
    assert "rn_passed_only_contract_expectations_no_runtime_change" in inventory["regression_test_targets"]
    assert "measurement_exit_gate_connection_not_product_gate_release" in inventory["regression_test_targets"]
    assert "exit_gate_four_fixture_semantics" in inventory["regression_test_targets"]

    lock_ids = {item["contract_id"] for item in inventory["contract_locks"]}
    assert "emotion_submit_route_stable" in lock_ids
    assert "input_feedback_comment_public_key_stable" in lock_ids
    assert "input_feedback_emlis_ai_status_stable" in lock_ids
    assert "rn_passed_only_modal_contract" in lock_ids
    assert "db_physical_name_boundary" in lock_ids
    assert "gate_fail_closed_boundary" in lock_ids
    assert "meta_only_diagnostic_boundary" in lock_ids
    assert "blind_qa_read_feeling_boundary" in lock_ids
    assert "next_action_routing_before_repair_boundary" in lock_ids
    assert "local_tool_output_meta_only_boundary" in lock_ids
    assert "step9_regression_public_contract_boundary" in lock_ids
    assert "step9_regression_counting_semantics_boundary" in lock_ids
    assert "step10_exit_gate_measurement_only_boundary" in lock_ids
    assert "step10_exit_gate_fact_based_next_action_boundary" in lock_ids
    assert "step10_exit_gate_not_product_gate_boundary" in lock_ids
    assert "step10_exit_gate_fixture_coverage_boundary" in lock_ids

    allowed = set(inventory["allowed_touch_files"])
    assert "ai/services/ai_inference/emlis_ai_observation_diagnostic_compare.py" in allowed
    assert "ai/services/ai_inference/emlis_ai_observation_diagnostic_branching.py" in allowed
    assert "ai/services/ai_inference/emlis_ai_complete_product_quality_measurement_connection.py" in allowed
    assert "ai/services/ai_inference/emlis_ai_complete_product_quality_scorecard_service.py" in allowed
    assert "ai/services/ai_inference/emlis_ai_complete_release_ladder_service.py" in allowed
    assert "ai/tests/test_emlis_ai_complete_product_quality_measurement_connection.py" in allowed
    assert "ai/tests/test_emlis_ai_complete_product_quality_scorecard.py" in allowed
    assert "ai/tests/test_emlis_ai_complete_product_quality_scorecard_blind_qa.py" in allowed
    assert "ai/tools/emlis_observation_product_quality_measurement.py" in allowed
    assert "ai/tests/test_emlis_observation_product_quality_measurement_tool_step8.py" in allowed
    assert "ai/tests/test_emlis_ai_complete_product_quality_measurement_regression_step9.py" in allowed
    assert "ai/tests/test_emlis_ai_complete_product_quality_measurement_exit_gate_step10.py" in allowed
    assert "ai/tests/contract/test_emlis_ai_contracts.py" in allowed
    assert "ai/tests/contract/test_rn_surface_guards.py" in allowed
    assert not any(path.startswith("screens/") for path in allowed)
    assert not any(path.startswith("Cocolon/screens/") for path in allowed)


def test_step0_contract_inventory_dump_is_meta_only_and_rejects_text_payload_keys() -> None:
    inventory = build_product_gate_measurement_contract_inventory()
    dumped = dump_product_gate_measurement_contract_inventory(inventory)
    parsed = json.loads(dumped)

    assert parsed["raw_input_included"] is False
    assert parsed["comment_text_included"] is False
    assert "これは出してはいけない本文" not in dumped

    unsafe = dict(inventory)
    unsafe["commentText"] = "これは出してはいけない本文"
    with pytest.raises(ValueError):
        assert_product_gate_measurement_contract_inventory_meta_only(unsafe)
