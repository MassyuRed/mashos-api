# -*- coding: utf-8 -*-
"""R4 tests for P7-HOLD-004 backend-suite group run result material."""

from __future__ import annotations

import json

import pytest

from emlis_ai_p7_contracts import assert_p7_no_body_payload_or_contract_mutation
from emlis_ai_p7_hold004_backend_suite_execution_results import (
    P7_HOLD004_BACKEND_R4_R5_SOURCE_SNAPSHOT_REF,
    P7_HOLD004_BACKEND_SUITE_BACKEND_SPLIT_COMPATIBLE_STATUS_BY_STATUS,
    P7_HOLD004_BACKEND_SUITE_GROUP_RUN_RESULT_SCHEMA_VERSION,
    P7_HOLD004_BACKEND_SUITE_SPLIT_CONSISTENCY_R4_R5_STEP,
    P7_HOLD004_BACKEND_SUITE_STATUS_COLLECTION_FAILED,
    P7_HOLD004_BACKEND_SUITE_STATUS_FAIL,
    P7_HOLD004_BACKEND_SUITE_STATUS_INTERRUPTED,
    P7_HOLD004_BACKEND_SUITE_STATUS_NOT_RUN,
    P7_HOLD004_BACKEND_SUITE_STATUS_PASS,
    P7_HOLD004_BACKEND_SUITE_STATUS_PASS_WITH_SKIPS,
    P7_HOLD004_BACKEND_SUITE_STATUS_TIMEOUT,
    P7_HOLD004_GROUP02_OFFICIAL_TEST_ITEM_COUNT,
    P7_HOLD004_OFFICIAL_CAPTURE_ADOPTION_STATUS_BLOCKED,
    P7_HOLD004_OFFICIAL_CAPTURE_ADOPTION_STATUS_GREEN,
    P7_HOLD004_OFFICIAL_CAPTURE_ADOPTION_STATUS_RECORDABLE_RED,
    P7_HOLD004_OFFICIAL_CAPTURE_ADOPTION_STATUS_RECORDABLE_TIMEOUT,
    P7_HOLD004_OFFICIAL_CAPTURE_ADOPTION_STATUS_REJECTED_BASELINE_MISMATCH,
    assert_p7_hold004_backend_suite_group_run_result_contract,
    assert_p7_hold004_official_group02_capture_adoption_decision_contract,
    assert_p7_hold004_official_group02_capture_adoption_rule_contract,
    build_p7_hold004_backend_suite_group_run_result,
    build_p7_hold004_official_group02_capture_adoption_decision,
    build_p7_hold004_official_group02_capture_adoption_rule,
    normalize_p7_hold004_backend_suite_group_run_status,
)
from emlis_ai_p7_hold004_backend_suite_group_inventory_plan import (
    P7_HOLD004_BACKEND_SUITE_EXECUTION_PLAN_ID,
    P7_HOLD004_BACKEND_SUITE_GROUP_INVENTORY_ID,
)
from emlis_ai_p7_hold004_backend_suite_split_consistency import P7_HOLD004_BACKEND_COLLECT_BASELINE_ID

_SAMPLE_COMMENT_BODY = "これはgroup run result materialへ入れてはいけない本文です"
_SAMPLE_TERMINAL_OUTPUT = "pytest terminal output and traceback must not be retained"


def test_r4_pass_group_run_result_claims_group_green_only_without_release_or_full_suite_promotion() -> None:
    result = build_p7_hold004_backend_suite_group_run_result(
        group_id="group_04_complete_product_quality",
        status=P7_HOLD004_BACKEND_SUITE_STATUS_PASS,
        passed=49,
    )

    assert result["schema_version"] == P7_HOLD004_BACKEND_SUITE_GROUP_RUN_RESULT_SCHEMA_VERSION
    assert result["phase"] == "P7_ProductQualityRunner_LongRunGate"
    assert result["step"] == P7_HOLD004_BACKEND_SUITE_SPLIT_CONSISTENCY_R4_R5_STEP
    assert result["implementation_step"] == P7_HOLD004_BACKEND_SUITE_SPLIT_CONSISTENCY_R4_R5_STEP
    assert result["hold_id"] == "P7-HOLD-004"
    assert result["plan_id"] == P7_HOLD004_BACKEND_SUITE_EXECUTION_PLAN_ID
    assert result["inventory_id"] == P7_HOLD004_BACKEND_SUITE_GROUP_INVENTORY_ID
    assert result["collect_baseline_id"] == P7_HOLD004_BACKEND_COLLECT_BASELINE_ID
    assert result["source_mode"] == "local_snapshot"
    assert result["source_snapshot_ref"] == P7_HOLD004_BACKEND_R4_R5_SOURCE_SNAPSHOT_REF
    assert result["git_checked"] is False
    assert result["current_collect_baseline_reconciled"] is True
    assert result["current_collect_baseline_connected"] is True
    assert result["current_group_inventory_connected"] is True
    assert result["current_execution_plan_connected"] is True
    assert result["previous_baseline_is_not_current"] is True
    assert result["old_baseline_not_used_as_current"] is True
    assert result["baseline_mismatch_blocks_execution"] is True

    assert result["group_id"] == "group_04_complete_product_quality"
    assert result["batch_id"] == "group_04_complete_product_quality_batch_01"
    assert result["run_kind"] == "capture_run"
    assert result["status"] == P7_HOLD004_BACKEND_SUITE_STATUS_PASS
    assert result["backend_split_compatible_status"] == "green_confirmed"
    assert result["timeout_budget_sec"] == 150
    assert result["observed_counts"] == {
        "passed": 49,
        "failed": 0,
        "skipped": 0,
        "warnings": 0,
        "errors": 0,
        "deselected": 0,
    }
    assert result["first_failure"]["present"] is False
    assert result["timeout_capture"]["present"] is False
    assert result["red_classification_required"] is False
    assert result["timeout_classification_required"] is False
    assert result["can_claim_group_green"] is True
    assert result["can_claim_full_backend_suite_green"] is False

    assert result["full_backend_suite_green_confirmed"] is False
    assert result["full_backend_suite_green_claim_allowed"] is False
    assert result["split_green_is_full_backend_suite_green"] is False
    assert result["split_green_can_close_p7_hold004"] is False
    assert result["hold004_close_allowed"] is False
    assert result["p7_complete"] is False
    assert result["p8_start_allowed"] is False
    assert result["release_allowed"] is False
    assert "P7-HOLD-004" in result["unresolved_hold_refs"]
    assert "full_backend_suite_green_unconfirmed" in result["required_followup_fixes"]

    assert result["raw_traceback_included"] is False
    assert result["terminal_output_retained"] is False
    assert result["stdout_retained"] is False
    assert result["stderr_retained"] is False
    assert all(value is False for value in result["public_contract"].values())
    assert all(value is False for value in result["body_free_markers"].values())
    assert result["body_free"] is True

    serialized = json.dumps(result, ensure_ascii=False, sort_keys=True)
    assert _SAMPLE_COMMENT_BODY not in serialized
    assert _SAMPLE_TERMINAL_OUTPUT not in serialized
    assert "terminal_output" not in result
    assert "stdout" not in result
    assert "stderr" not in result
    assert "traceback" not in result

    official_rule = build_p7_hold004_official_group02_capture_adoption_rule()
    assert official_rule["group_id"] == "group_02_p7_hold004"
    assert official_rule["batch_id"] == "group_02_p7_hold004_batch_01"
    assert official_rule["expected_group_file_count"] == 19
    assert official_rule["expected_group_test_item_count"] == P7_HOLD004_GROUP02_OFFICIAL_TEST_ITEM_COUNT
    assert official_rule["expected_collect_only_test_item_count"] == P7_HOLD004_GROUP02_OFFICIAL_TEST_ITEM_COUNT
    assert official_rule["expected_warning_count"] == 1
    assert official_rule["first_capture_group_id"] == "group_02_p7_hold004"
    assert official_rule["official_capture_run_executed"] is False
    assert official_rule["official_capture_result_recorded"] is False
    assert official_rule["can_claim_group_green"] is False
    assert official_rule["can_claim_full_backend_suite_green"] is False
    assert official_rule["release_allowed"] is False
    assert official_rule["body_free"] is True
    assert all(official_rule["capture_adoption_conditions"].values())
    assert_p7_hold004_official_group02_capture_adoption_rule_contract(official_rule)

    official_group02_result = build_p7_hold004_backend_suite_group_run_result(
        group_id="group_02_p7_hold004",
        status=P7_HOLD004_BACKEND_SUITE_STATUS_PASS,
        passed=P7_HOLD004_GROUP02_OFFICIAL_TEST_ITEM_COUNT,
        warnings=1,
    )
    official_decision = build_p7_hold004_official_group02_capture_adoption_decision(
        run_result=official_group02_result
    )
    assert official_decision["adoption_status"] == P7_HOLD004_OFFICIAL_CAPTURE_ADOPTION_STATUS_GREEN
    assert official_decision["official_capture_material_recordable"] is True
    assert official_decision["official_group_02_capture_recorded"] is True
    assert official_decision["official_group_02_capture_green_confirmed"] is True
    assert official_decision["can_claim_group_green"] is True
    assert official_decision["can_claim_full_backend_suite_green"] is False
    assert official_decision["full_backend_suite_green_confirmed"] is False
    assert official_decision["hold004_close_allowed"] is False
    assert official_decision["p7_complete"] is False
    assert official_decision["p8_start_allowed"] is False
    assert official_decision["release_allowed"] is False
    assert official_decision["adoption_blockers"] == []
    assert "group_02_green_is_not_full_backend_suite_green" in official_decision["required_followup_fixes"]
    assert official_decision["terminal_output_retained"] is False
    assert official_decision["stdout_retained"] is False
    assert official_decision["stderr_retained"] is False
    assert official_decision["raw_traceback_included"] is False
    assert_p7_hold004_official_group02_capture_adoption_decision_contract(official_decision)

    assert_p7_hold004_backend_suite_group_run_result_contract(result)
    assert_p7_no_body_payload_or_contract_mutation(result, source="r4_pass_group_result_test")


def test_r4_pass_with_skips_keeps_skips_separate_from_plain_pass_and_full_suite_green() -> None:
    result = build_p7_hold004_backend_suite_group_run_result(
        group_id="group_05_user_label_connection_p5",
        pytest_exit_code=0,
        passed=180,
        skipped=2,
    )

    assert result["status"] == P7_HOLD004_BACKEND_SUITE_STATUS_PASS_WITH_SKIPS
    assert result["backend_split_compatible_status"] == "green_confirmed"
    assert result["observed_counts"]["skipped"] == 2
    assert result["can_claim_group_green"] is True
    assert result["can_claim_full_backend_suite_green"] is False
    assert "group_green_with_skips_is_not_full_backend_suite_green" in result["required_followup_fixes"]
    assert_p7_hold004_backend_suite_group_run_result_contract(result)


def test_r4_fail_group_run_result_captures_first_failure_identifiers_only_and_requires_red_classification() -> None:
    result = build_p7_hold004_backend_suite_group_run_result(
        group_id="group_08_complete_initial",
        status=P7_HOLD004_BACKEND_SUITE_STATUS_FAIL,
        passed=3,
        failed=1,
        first_failure_nodeid="tests/test_emlis_ai_complete_initial_example.py::test_public_shape_contract",
        first_failure_file_ref="tests/test_emlis_ai_complete_initial_example.py",
        failure_kind="assertion_failure",
        owner_layer_candidate="emlis_complete_initial",
    )

    assert result["status"] == P7_HOLD004_BACKEND_SUITE_STATUS_FAIL
    assert result["backend_split_compatible_status"] == "red_until_repaired"
    assert result["can_claim_group_green"] is False
    assert result["can_claim_full_backend_suite_green"] is False
    assert result["red_classification_required"] is True
    assert result["timeout_classification_required"] is False
    assert result["first_failure"] == {
        "present": True,
        "nodeid": "tests/test_emlis_ai_complete_initial_example.py::test_public_shape_contract",
        "file_ref": "tests/test_emlis_ai_complete_initial_example.py",
        "failure_kind": "assertion_failure",
        "owner_layer_candidate": "emlis_complete_initial",
    }
    assert result["timeout_capture"]["present"] is False
    assert "first_red_classification_required" in result["required_followup_fixes"]
    assert "backend_suite_group_failed" in result["reason_codes"]
    assert "traceback" not in result
    assert "terminal_output" not in result

    official_fail = build_p7_hold004_backend_suite_group_run_result(
        group_id="group_02_p7_hold004",
        status=P7_HOLD004_BACKEND_SUITE_STATUS_FAIL,
        passed=251,
        failed=1,
        first_failure_nodeid="tests/test_emlis_ai_p7_hold004_example.py::test_current_snapshot_contract",
        first_failure_file_ref="tests/test_emlis_ai_p7_hold004_example.py",
        failure_kind="assertion_failed_or_contract_mismatch",
        owner_layer_candidate="p7_hold004_target",
    )
    official_fail_decision = build_p7_hold004_official_group02_capture_adoption_decision(
        run_result=official_fail
    )
    assert official_fail_decision["adoption_status"] == P7_HOLD004_OFFICIAL_CAPTURE_ADOPTION_STATUS_RECORDABLE_RED
    assert official_fail_decision["official_capture_material_recordable"] is True
    assert official_fail_decision["official_group_02_capture_green_confirmed"] is False
    assert official_fail_decision["red_classification_required"] is True
    assert official_fail_decision["can_claim_group_green"] is False
    assert official_fail_decision["can_claim_full_backend_suite_green"] is False
    assert official_fail_decision["release_allowed"] is False
    assert "first_red_classification_required" in official_fail_decision["required_followup_fixes"]
    assert_p7_hold004_official_group02_capture_adoption_decision_contract(official_fail_decision)

    assert_p7_hold004_backend_suite_group_run_result_contract(result)


def test_r4_timeout_group_run_result_isolated_as_not_green_and_body_free() -> None:
    result = build_p7_hold004_backend_suite_group_run_result(
        group_id="group_11_emlis_runtime_other",
        batch_id="group_11_emlis_runtime_other_batch_03",
        timed_out=True,
        elapsed_sec_bucket="over_budget",
        last_known_phase="run",
    )

    assert result["status"] == P7_HOLD004_BACKEND_SUITE_STATUS_TIMEOUT
    assert result["backend_split_compatible_status"] == "timeout_isolated"
    assert result["timeout_budget_sec"] == 240
    assert result["timeout_capture"] == {
        "present": True,
        "elapsed_sec_bucket": "over_budget",
        "last_known_phase": "run",
        "first_timeout_capture": True,
        "slow_group_candidate": True,
    }
    assert result["first_failure"]["present"] is False
    assert result["can_claim_group_green"] is False
    assert result["can_claim_full_backend_suite_green"] is False
    assert result["timeout_classification_required"] is True
    assert "timeout_isolated_not_green" in result["required_followup_fixes"]
    assert "timeout_classification_required" in result["required_followup_fixes"]
    assert result["full_backend_suite_green_confirmed"] is False

    official_timeout = build_p7_hold004_backend_suite_group_run_result(
        group_id="group_02_p7_hold004",
        timed_out=True,
        elapsed_sec_bucket="over_budget",
        last_known_phase="run",
    )
    official_timeout_decision = build_p7_hold004_official_group02_capture_adoption_decision(
        run_result=official_timeout
    )
    assert official_timeout_decision["adoption_status"] == P7_HOLD004_OFFICIAL_CAPTURE_ADOPTION_STATUS_RECORDABLE_TIMEOUT
    assert official_timeout_decision["official_capture_material_recordable"] is True
    assert official_timeout_decision["official_group_02_capture_green_confirmed"] is False
    assert official_timeout_decision["timeout_classification_required"] is True
    assert official_timeout_decision["can_claim_group_green"] is False
    assert official_timeout_decision["release_allowed"] is False
    assert "timeout_isolated_not_green" in official_timeout_decision["required_followup_fixes"]
    assert_p7_hold004_official_group02_capture_adoption_decision_contract(official_timeout_decision)

    assert_p7_hold004_backend_suite_group_run_result_contract(result)


@pytest.mark.parametrize(
    ("kwargs", "expected_status"),
    (
        ({"pytest_exit_code": 0, "passed": 10}, P7_HOLD004_BACKEND_SUITE_STATUS_PASS),
        ({"pytest_exit_code": 0, "passed": 10, "skipped": 1}, P7_HOLD004_BACKEND_SUITE_STATUS_PASS_WITH_SKIPS),
        ({"pytest_exit_code": 2}, P7_HOLD004_BACKEND_SUITE_STATUS_INTERRUPTED),
        ({"pytest_exit_code": 4}, P7_HOLD004_BACKEND_SUITE_STATUS_COLLECTION_FAILED),
        ({"timed_out": True}, P7_HOLD004_BACKEND_SUITE_STATUS_TIMEOUT),
    ),
)
def test_r4_status_normalizer_maps_pytest_outcomes(kwargs: dict[str, object], expected_status: str) -> None:
    assert normalize_p7_hold004_backend_suite_group_run_status(**kwargs) == expected_status


def test_r4_status_normalizer_maps_fail_when_failure_counts_are_present() -> None:
    assert (
        normalize_p7_hold004_backend_suite_group_run_status(
            observed_counts={"failed": 1, "passed": 2, "skipped": 0, "warnings": 0, "errors": 0, "deselected": 0}
        )
        == P7_HOLD004_BACKEND_SUITE_STATUS_FAIL
    )


def test_r4_collection_failed_and_not_run_materials_keep_release_closed() -> None:
    collection_failed = build_p7_hold004_backend_suite_group_run_result(
        group_id="group_02_p7_hold004",
        status=P7_HOLD004_BACKEND_SUITE_STATUS_COLLECTION_FAILED,
    )
    not_run = build_p7_hold004_backend_suite_group_run_result(
        group_id="group_02_p7_hold004",
        status=P7_HOLD004_BACKEND_SUITE_STATUS_NOT_RUN,
    )

    assert collection_failed["status"] == P7_HOLD004_BACKEND_SUITE_STATUS_COLLECTION_FAILED
    assert collection_failed["backend_split_compatible_status"] == "blocked"
    assert collection_failed["can_claim_group_green"] is False
    assert "collection_failed_blocks_execution" in collection_failed["required_followup_fixes"]

    assert not_run["status"] == P7_HOLD004_BACKEND_SUITE_STATUS_NOT_RUN
    assert not_run["run_kind"] == "not_run"
    assert not_run["backend_split_compatible_status"] == "not_run"
    assert not_run["can_claim_group_green"] is False
    assert "backend_suite_group_execution_not_run" in not_run["required_followup_fixes"]

    assert collection_failed["release_allowed"] is False
    assert not_run["release_allowed"] is False

    no_result_decision = build_p7_hold004_official_group02_capture_adoption_decision()
    assert no_result_decision["adoption_status"] == P7_HOLD004_OFFICIAL_CAPTURE_ADOPTION_STATUS_BLOCKED
    assert no_result_decision["official_capture_material_recordable"] is False
    assert no_result_decision["official_group_02_capture_recorded"] is False
    assert no_result_decision["can_claim_group_green"] is False
    assert no_result_decision["release_allowed"] is False
    assert "official_group_02_capture_run_not_recorded" in no_result_decision["adoption_blockers"]
    assert_p7_hold004_official_group02_capture_adoption_decision_contract(no_result_decision)

    old_baseline_result = build_p7_hold004_backend_suite_group_run_result(
        group_id="group_02_p7_hold004",
        status=P7_HOLD004_BACKEND_SUITE_STATUS_PASS,
        passed=P7_HOLD004_GROUP02_OFFICIAL_TEST_ITEM_COUNT,
        warnings=1,
    )
    old_baseline_result["collect_baseline_id"] = "p7_hold004_backend_collect_baseline_20260614"
    rejected_decision = build_p7_hold004_official_group02_capture_adoption_decision(
        run_result=old_baseline_result
    )
    assert rejected_decision["adoption_status"] == P7_HOLD004_OFFICIAL_CAPTURE_ADOPTION_STATUS_REJECTED_BASELINE_MISMATCH
    assert rejected_decision["official_capture_material_recordable"] is False
    assert rejected_decision["official_group_02_capture_green_confirmed"] is False
    assert rejected_decision["can_claim_group_green"] is False
    assert rejected_decision["release_allowed"] is False
    assert "collect_baseline_id_mismatch" in rejected_decision["adoption_blockers"]
    assert_p7_hold004_official_group02_capture_adoption_decision_contract(rejected_decision)

    assert_p7_hold004_backend_suite_group_run_result_contract(collection_failed)
    assert_p7_hold004_backend_suite_group_run_result_contract(not_run)


@pytest.mark.parametrize(
    ("field", "bad_value"),
    (
        ("full_backend_suite_green_confirmed", True),
        ("full_backend_suite_green_claim_allowed", True),
        ("split_green_is_full_backend_suite_green", True),
        ("split_green_can_close_p7_hold004", True),
        ("hold004_close_allowed", True),
        ("p7_complete", True),
        ("p8_start_allowed", True),
        ("release_allowed", True),
        ("body_free", False),
        ("can_claim_full_backend_suite_green", True),
        ("raw_traceback_included", True),
        ("terminal_output_retained", True),
        ("stdout_retained", True),
        ("stderr_retained", True),
    ),
)
def test_r4_group_run_result_contract_rejects_release_body_or_full_suite_mutation(field: str, bad_value: object) -> None:
    result = build_p7_hold004_backend_suite_group_run_result(
        group_id="group_04_complete_product_quality",
        status=P7_HOLD004_BACKEND_SUITE_STATUS_PASS,
        passed=49,
    )
    result[field] = bad_value

    with pytest.raises(ValueError):
        assert_p7_hold004_backend_suite_group_run_result_contract(result)


@pytest.mark.parametrize(
    "marker_key",
    (
        "raw_input_included",
        "history_raw_text_included",
        "comment_text_body_included",
        "candidate_body_included",
        "surface_body_included",
        "reviewer_free_text_included",
        "terminal_output_included",
    ),
)
def test_r4_group_run_result_contract_rejects_body_free_marker_or_payload(marker_key: str) -> None:
    result = build_p7_hold004_backend_suite_group_run_result(
        group_id="group_04_complete_product_quality",
        status=P7_HOLD004_BACKEND_SUITE_STATUS_PASS,
        passed=49,
    )
    result["body_free_markers"][marker_key] = True
    with pytest.raises(ValueError):
        assert_p7_hold004_backend_suite_group_run_result_contract(result)

    result = build_p7_hold004_backend_suite_group_run_result(
        group_id="group_04_complete_product_quality",
        status=P7_HOLD004_BACKEND_SUITE_STATUS_PASS,
        passed=49,
    )
    result["terminal_output"] = _SAMPLE_TERMINAL_OUTPUT
    with pytest.raises(ValueError):
        assert_p7_hold004_backend_suite_group_run_result_contract(result)


def test_r4_group_run_result_contract_rejects_fail_without_body_free_first_failure_identifiers() -> None:
    result = build_p7_hold004_backend_suite_group_run_result(
        group_id="group_08_complete_initial",
        status=P7_HOLD004_BACKEND_SUITE_STATUS_FAIL,
        passed=3,
        failed=1,
        first_failure_nodeid="tests/test_emlis_ai_complete_initial_example.py::test_public_shape_contract",
        first_failure_file_ref="tests/test_emlis_ai_complete_initial_example.py",
        failure_kind="assertion_failure",
        owner_layer_candidate="emlis_complete_initial",
    )
    result["first_failure"]["nodeid"] = ""

    with pytest.raises(ValueError):
        assert_p7_hold004_backend_suite_group_run_result_contract(result)


def test_r4_group_run_result_contract_rejects_timeout_without_timeout_capture() -> None:
    result = build_p7_hold004_backend_suite_group_run_result(
        group_id="group_11_emlis_runtime_other",
        batch_id="group_11_emlis_runtime_other_batch_03",
        timed_out=True,
    )
    result["timeout_capture"]["present"] = False

    with pytest.raises(ValueError):
        assert_p7_hold004_backend_suite_group_run_result_contract(result)


@pytest.mark.parametrize(
    ("mutation", "bad_value"),
    (
        ("group_id", "group_99_missing"),
        ("batch_id", "group_11_emlis_runtime_other_batch_99"),
        ("status", "PARTIAL"),
        ("backend_split_compatible_status", "full_backend_suite_green"),
        ("run_kind", "background_run"),
        ("expected_batch_ids", ["other_batch"]),
    ),
)
def test_r4_group_run_result_contract_rejects_group_batch_status_or_run_kind_mutation(
    mutation: str, bad_value: object
) -> None:
    result = build_p7_hold004_backend_suite_group_run_result(
        group_id="group_11_emlis_runtime_other",
        batch_id="group_11_emlis_runtime_other_batch_03",
        timed_out=True,
    )
    result[mutation] = bad_value

    with pytest.raises(ValueError):
        assert_p7_hold004_backend_suite_group_run_result_contract(result)


def test_r4_group_run_result_contract_rejects_pass_with_failure_counts_or_skips_mismatch() -> None:
    result = build_p7_hold004_backend_suite_group_run_result(
        group_id="group_04_complete_product_quality",
        status=P7_HOLD004_BACKEND_SUITE_STATUS_PASS,
        passed=49,
    )
    result["observed_counts"]["failed"] = 1
    with pytest.raises(ValueError):
        assert_p7_hold004_backend_suite_group_run_result_contract(result)

    result = build_p7_hold004_backend_suite_group_run_result(
        group_id="group_05_user_label_connection_p5",
        status=P7_HOLD004_BACKEND_SUITE_STATUS_PASS_WITH_SKIPS,
        passed=180,
        skipped=2,
    )
    result["observed_counts"]["skipped"] = 0
    with pytest.raises(ValueError):
        assert_p7_hold004_backend_suite_group_run_result_contract(result)


def test_r4_backend_split_compatible_status_map_is_complete_for_allowed_statuses() -> None:
    expected = {
        P7_HOLD004_BACKEND_SUITE_STATUS_PASS: "green_confirmed",
        P7_HOLD004_BACKEND_SUITE_STATUS_PASS_WITH_SKIPS: "green_confirmed",
        P7_HOLD004_BACKEND_SUITE_STATUS_FAIL: "red_until_repaired",
        P7_HOLD004_BACKEND_SUITE_STATUS_TIMEOUT: "timeout_isolated",
        P7_HOLD004_BACKEND_SUITE_STATUS_COLLECTION_FAILED: "blocked",
        P7_HOLD004_BACKEND_SUITE_STATUS_NOT_RUN: "not_run",
        P7_HOLD004_BACKEND_SUITE_STATUS_INTERRUPTED: "blocked",
    }
    for status, compatible in expected.items():
        assert P7_HOLD004_BACKEND_SUITE_BACKEND_SPLIT_COMPATIBLE_STATUS_BY_STATUS[status] == compatible
