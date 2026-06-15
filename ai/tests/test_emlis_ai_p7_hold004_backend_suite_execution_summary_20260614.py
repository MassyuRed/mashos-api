# -*- coding: utf-8 -*-
"""R5 tests for P7-HOLD-004 backend-suite execution summary material."""

from __future__ import annotations

import json

import pytest

from emlis_ai_p7_contracts import assert_p7_no_body_payload_or_contract_mutation
from emlis_ai_p7_hold004_backend_suite_execution_results import (
    P7_HOLD004_BACKEND_R4_R5_SOURCE_SNAPSHOT_REF,
    P7_HOLD004_BACKEND_SUITE_EXECUTION_SUMMARY_ID,
    P7_HOLD004_BACKEND_SUITE_EXECUTION_SUMMARY_SCHEMA_VERSION,
    P7_HOLD004_BACKEND_SUITE_SPLIT_CONSISTENCY_R4_R5_STEP,
    P7_HOLD004_BACKEND_SUITE_STATUS_FAIL,
    P7_HOLD004_BACKEND_SUITE_STATUS_NOT_RUN,
    P7_HOLD004_BACKEND_SUITE_STATUS_PASS,
    P7_HOLD004_BACKEND_SUITE_STATUS_PASS_WITH_SKIPS,
    P7_HOLD004_BACKEND_SUITE_STATUS_TIMEOUT,
    assert_p7_hold004_backend_suite_execution_summary_contract,
    build_p7_hold004_backend_suite_execution_summary,
    build_p7_hold004_backend_suite_group_run_result,
)
from emlis_ai_p7_hold004_backend_suite_group_inventory_plan import (
    P7_HOLD004_BACKEND_SUITE_EXECUTION_ORDER,
    P7_HOLD004_BACKEND_SUITE_EXECUTION_PLAN_ID,
    P7_HOLD004_BACKEND_SUITE_GROUP_DEFINITIONS,
    P7_HOLD004_BACKEND_SUITE_GROUP_IDS,
    P7_HOLD004_BACKEND_SUITE_GROUP_INVENTORY_ID,
)
from emlis_ai_p7_hold004_backend_suite_split_consistency import P7_HOLD004_BACKEND_COLLECT_BASELINE_ID

_SAMPLE_COMMENT_BODY = "これはexecution summary materialへ入れてはいけない本文です"
_SAMPLE_TERMINAL_OUTPUT = "pytest terminal output should not be retained"


def _planned_batch_ids(group_id: str) -> list[str]:
    for definition in P7_HOLD004_BACKEND_SUITE_GROUP_DEFINITIONS:
        if definition["group_id"] == group_id:
            return [f"{group_id}_batch_{index:02d}" for index in range(1, int(definition["planned_batch_count"]) + 1)]
    raise AssertionError(f"missing definition: {group_id}")


def _all_green_results_with_one_skip() -> list[dict[str, object]]:
    results: list[dict[str, object]] = []
    for group_id in P7_HOLD004_BACKEND_SUITE_GROUP_IDS:
        for batch_id in _planned_batch_ids(group_id):
            status = P7_HOLD004_BACKEND_SUITE_STATUS_PASS
            skipped = 0
            if group_id == "group_05_user_label_connection_p5":
                status = P7_HOLD004_BACKEND_SUITE_STATUS_PASS_WITH_SKIPS
                skipped = 1
            results.append(
                build_p7_hold004_backend_suite_group_run_result(
                    group_id=group_id,
                    batch_id=batch_id,
                    status=status,
                    passed=1,
                    skipped=skipped,
                )
            )
    return results


def test_r5_default_execution_summary_keeps_all_groups_not_run_and_hold004_open() -> None:
    summary = build_p7_hold004_backend_suite_execution_summary()

    assert summary["schema_version"] == P7_HOLD004_BACKEND_SUITE_EXECUTION_SUMMARY_SCHEMA_VERSION
    assert summary["phase"] == "P7_ProductQualityRunner_LongRunGate"
    assert summary["step"] == P7_HOLD004_BACKEND_SUITE_SPLIT_CONSISTENCY_R4_R5_STEP
    assert summary["implementation_step"] == P7_HOLD004_BACKEND_SUITE_SPLIT_CONSISTENCY_R4_R5_STEP
    assert summary["hold_id"] == "P7-HOLD-004"
    assert summary["summary_id"] == P7_HOLD004_BACKEND_SUITE_EXECUTION_SUMMARY_ID
    assert summary["collect_baseline_id"] == P7_HOLD004_BACKEND_COLLECT_BASELINE_ID
    assert summary["inventory_id"] == P7_HOLD004_BACKEND_SUITE_GROUP_INVENTORY_ID
    assert summary["plan_id"] == P7_HOLD004_BACKEND_SUITE_EXECUTION_PLAN_ID
    assert summary["source_mode"] == "local_snapshot"
    assert summary["source_snapshot_ref"] == P7_HOLD004_BACKEND_R4_R5_SOURCE_SNAPSHOT_REF
    assert summary["git_checked"] is False
    assert summary["current_collect_baseline_reconciled"] is True
    assert summary["current_collect_baseline_connected"] is True
    assert summary["current_group_inventory_connected"] is True
    assert summary["current_execution_plan_connected"] is True
    assert summary["previous_baseline_is_not_current"] is True
    assert summary["old_baseline_not_used_as_current"] is True
    assert summary["baseline_mismatch_blocks_execution"] is True

    assert summary["expected_group_count"] == 13
    assert summary["expected_total_batch_count"] == 19
    assert summary["recorded_run_result_count"] == 0
    assert summary["recorded_batch_statuses"] == []
    assert summary["group_statuses"] == {
        group_id: P7_HOLD004_BACKEND_SUITE_STATUS_NOT_RUN for group_id in P7_HOLD004_BACKEND_SUITE_GROUP_IDS
    }
    assert summary["green_group_ids"] == []
    assert summary["failed_group_ids"] == []
    assert summary["timeout_group_ids"] == []
    assert summary["not_run_group_ids"] == list(P7_HOLD004_BACKEND_SUITE_GROUP_IDS)
    assert summary["partial_group_ids"] == []
    assert summary["all_groups_executed"] is False
    assert summary["split_all_groups_green_confirmed"] is False
    assert summary["first_red"]["present"] is False
    assert summary["first_timeout"]["present"] is False
    assert summary["group_run_results_recorded"] is False

    assert summary["full_backend_suite_green_confirmed"] is False
    assert summary["full_backend_suite_green_claim_allowed"] is False
    assert summary["split_green_is_full_backend_suite_green"] is False
    assert summary["split_green_can_close_p7_hold004"] is False
    assert summary["hold004_close_allowed"] is False
    assert summary["p7_complete"] is False
    assert summary["p8_start_allowed"] is False
    assert summary["release_allowed"] is False
    assert "P7-HOLD-004" in summary["unresolved_hold_refs"]
    assert "backend_suite_group_execution_not_run" in summary["required_followup_fixes"]
    assert "full_backend_suite_green_unconfirmed" in summary["required_followup_fixes"]

    assert summary["raw_traceback_included"] is False
    assert summary["terminal_output_retained"] is False
    assert summary["stdout_retained"] is False
    assert summary["stderr_retained"] is False
    assert all(value is False for value in summary["public_contract"].values())
    assert all(value is False for value in summary["body_free_markers"].values())
    assert summary["body_free"] is True

    serialized = json.dumps(summary, ensure_ascii=False, sort_keys=True)
    assert _SAMPLE_COMMENT_BODY not in serialized
    assert _SAMPLE_TERMINAL_OUTPUT not in serialized
    assert "terminal_output" not in summary
    assert "stdout" not in summary
    assert "stderr" not in summary
    assert "traceback" not in summary

    assert_p7_hold004_backend_suite_execution_summary_contract(summary)
    assert_p7_no_body_payload_or_contract_mutation(summary, source="r5_default_summary_test")


def test_r5_execution_summary_aggregates_one_green_group_without_promoting_full_suite() -> None:
    group_02_pass = build_p7_hold004_backend_suite_group_run_result(
        group_id="group_02_p7_hold004",
        status=P7_HOLD004_BACKEND_SUITE_STATUS_PASS,
        passed=252,
    )
    summary = build_p7_hold004_backend_suite_execution_summary(run_results=[group_02_pass])

    assert summary["group_statuses"]["group_02_p7_hold004"] == P7_HOLD004_BACKEND_SUITE_STATUS_PASS
    assert summary["green_group_ids"] == ["group_02_p7_hold004"]
    assert "group_02_p7_hold004" not in summary["not_run_group_ids"]
    assert len(summary["not_run_group_ids"]) == 12
    assert summary["recorded_run_result_count"] == 1
    assert summary["recorded_batch_statuses"] == [
        {
            "group_id": "group_02_p7_hold004",
            "batch_id": "group_02_p7_hold004_batch_01",
            "status": P7_HOLD004_BACKEND_SUITE_STATUS_PASS,
        }
    ]
    assert summary["all_groups_executed"] is False
    assert summary["split_all_groups_green_confirmed"] is False
    assert summary["full_backend_suite_green_confirmed"] is False
    assert summary["hold004_close_allowed"] is False
    assert summary["release_allowed"] is False
    assert_p7_hold004_backend_suite_execution_summary_contract(summary)


def test_r5_execution_summary_all_split_groups_green_still_does_not_claim_full_backend_suite_green() -> None:
    summary = build_p7_hold004_backend_suite_execution_summary(run_results=_all_green_results_with_one_skip())

    assert summary["recorded_run_result_count"] == 19
    assert summary["all_groups_executed"] is True
    assert summary["split_all_groups_green_confirmed"] is True
    assert summary["green_group_ids"] == list(P7_HOLD004_BACKEND_SUITE_GROUP_IDS)
    assert summary["failed_group_ids"] == []
    assert summary["timeout_group_ids"] == []
    assert summary["not_run_group_ids"] == []
    assert summary["partial_group_ids"] == []
    assert summary["group_statuses"]["group_05_user_label_connection_p5"] == P7_HOLD004_BACKEND_SUITE_STATUS_PASS_WITH_SKIPS
    assert all(
        status in {P7_HOLD004_BACKEND_SUITE_STATUS_PASS, P7_HOLD004_BACKEND_SUITE_STATUS_PASS_WITH_SKIPS}
        for status in summary["group_statuses"].values()
    )

    assert summary["full_backend_suite_green_confirmed"] is False
    assert summary["full_backend_suite_green_claim_allowed"] is False
    assert summary["split_green_is_full_backend_suite_green"] is False
    assert summary["split_green_can_close_p7_hold004"] is False
    assert summary["hold004_close_allowed"] is False
    assert summary["p7_complete"] is False
    assert summary["p8_start_allowed"] is False
    assert summary["release_allowed"] is False
    assert "split_green_is_not_full_backend_suite_green" in summary["required_followup_fixes"]
    assert "un_split_full_backend_suite_green_not_confirmed" in summary["required_followup_fixes"]
    assert "full_backend_suite_green_unconfirmed" in summary["required_followup_fixes"]
    assert_p7_hold004_backend_suite_execution_summary_contract(summary)


def test_r5_execution_summary_captures_first_red_and_first_timeout_without_terminal_output() -> None:
    group_04_fail = build_p7_hold004_backend_suite_group_run_result(
        group_id="group_04_complete_product_quality",
        status=P7_HOLD004_BACKEND_SUITE_STATUS_FAIL,
        passed=10,
        failed=1,
        first_failure_nodeid="tests/test_emlis_ai_complete_product_quality_example.py::test_connection_contract",
        first_failure_file_ref="tests/test_emlis_ai_complete_product_quality_example.py",
        failure_kind="assertion_failure",
        owner_layer_candidate="complete_product_quality",
    )
    group_10_timeout = build_p7_hold004_backend_suite_group_run_result(
        group_id="group_10_two_stage_public_recovery",
        batch_id="group_10_two_stage_public_recovery_batch_02",
        timed_out=True,
        elapsed_sec_bucket="over_budget",
        last_known_phase="run",
    )
    summary = build_p7_hold004_backend_suite_execution_summary(run_results=[group_10_timeout, group_04_fail])

    assert summary["failed_group_ids"] == ["group_04_complete_product_quality"]
    assert summary["timeout_group_ids"] == ["group_10_two_stage_public_recovery"]
    assert summary["group_statuses"]["group_04_complete_product_quality"] == P7_HOLD004_BACKEND_SUITE_STATUS_FAIL
    assert summary["group_statuses"]["group_10_two_stage_public_recovery"] == P7_HOLD004_BACKEND_SUITE_STATUS_TIMEOUT
    assert summary["all_groups_executed"] is False
    assert summary["split_all_groups_green_confirmed"] is False

    assert summary["first_red"] == {
        "present": True,
        "group_id": "group_04_complete_product_quality",
        "batch_id": "group_04_complete_product_quality_batch_01",
        "nodeid": "tests/test_emlis_ai_complete_product_quality_example.py::test_connection_contract",
        "file_ref": "tests/test_emlis_ai_complete_product_quality_example.py",
        "failure_kind": "assertion_failure",
        "owner_layer_candidate": "complete_product_quality",
    }
    assert summary["first_timeout"] == {
        "present": True,
        "group_id": "group_10_two_stage_public_recovery",
        "batch_id": "group_10_two_stage_public_recovery_batch_02",
        "timeout_budget_sec": 180,
        "elapsed_sec_bucket": "over_budget",
        "last_known_phase": "run",
    }
    assert "first_red_classification_required" in summary["required_followup_fixes"]
    assert "timeout_classification_required" in summary["required_followup_fixes"]
    assert summary["full_backend_suite_green_confirmed"] is False
    assert summary["release_allowed"] is False
    assert "terminal_output" not in summary
    assert "traceback" not in summary
    assert_p7_hold004_backend_suite_execution_summary_contract(summary)


def test_r5_execution_summary_keeps_partial_group_not_green_when_only_some_batches_are_recorded() -> None:
    partial_group_11 = build_p7_hold004_backend_suite_group_run_result(
        group_id="group_11_emlis_runtime_other",
        batch_id="group_11_emlis_runtime_other_batch_01",
        status=P7_HOLD004_BACKEND_SUITE_STATUS_PASS,
        passed=200,
    )
    summary = build_p7_hold004_backend_suite_execution_summary(run_results=[partial_group_11])

    assert summary["group_statuses"]["group_11_emlis_runtime_other"] == P7_HOLD004_BACKEND_SUITE_STATUS_NOT_RUN
    assert summary["partial_group_ids"] == ["group_11_emlis_runtime_other"]
    assert "group_11_emlis_runtime_other" in summary["not_run_group_ids"]
    assert "group_11_emlis_runtime_other" not in summary["green_group_ids"]
    assert summary["all_groups_executed"] is False
    assert summary["split_all_groups_green_confirmed"] is False
    assert "backend_suite_group_execution_partial" in summary["required_followup_fixes"]
    assert_p7_hold004_backend_suite_execution_summary_contract(summary)


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
        ("raw_traceback_included", True),
        ("terminal_output_retained", True),
        ("stdout_retained", True),
        ("stderr_retained", True),
    ),
)
def test_r5_execution_summary_contract_rejects_release_body_or_full_suite_mutation(field: str, bad_value: object) -> None:
    summary = build_p7_hold004_backend_suite_execution_summary()
    summary[field] = bad_value

    with pytest.raises(ValueError):
        assert_p7_hold004_backend_suite_execution_summary_contract(summary)


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
def test_r5_execution_summary_contract_rejects_body_free_marker_or_payload(marker_key: str) -> None:
    summary = build_p7_hold004_backend_suite_execution_summary()
    summary["body_free_markers"][marker_key] = True
    with pytest.raises(ValueError):
        assert_p7_hold004_backend_suite_execution_summary_contract(summary)

    summary = build_p7_hold004_backend_suite_execution_summary()
    summary["terminal_output"] = _SAMPLE_TERMINAL_OUTPUT
    with pytest.raises(ValueError):
        assert_p7_hold004_backend_suite_execution_summary_contract(summary)


def test_r5_execution_summary_contract_rejects_status_list_mismatch() -> None:
    summary = build_p7_hold004_backend_suite_execution_summary()
    summary["group_statuses"]["group_02_p7_hold004"] = P7_HOLD004_BACKEND_SUITE_STATUS_PASS
    with pytest.raises(ValueError):
        assert_p7_hold004_backend_suite_execution_summary_contract(summary)

    summary = build_p7_hold004_backend_suite_execution_summary()
    summary["not_run_group_ids"] = []
    with pytest.raises(ValueError):
        assert_p7_hold004_backend_suite_execution_summary_contract(summary)


def test_r5_execution_summary_contract_rejects_first_red_or_timeout_mismatch() -> None:
    fail_result = build_p7_hold004_backend_suite_group_run_result(
        group_id="group_04_complete_product_quality",
        status=P7_HOLD004_BACKEND_SUITE_STATUS_FAIL,
        passed=10,
        failed=1,
        first_failure_nodeid="tests/test_emlis_ai_complete_product_quality_example.py::test_connection_contract",
        first_failure_file_ref="tests/test_emlis_ai_complete_product_quality_example.py",
        failure_kind="assertion_failure",
        owner_layer_candidate="complete_product_quality",
    )
    summary = build_p7_hold004_backend_suite_execution_summary(run_results=[fail_result])
    summary["first_red"]["present"] = False
    with pytest.raises(ValueError):
        assert_p7_hold004_backend_suite_execution_summary_contract(summary)

    timeout_result = build_p7_hold004_backend_suite_group_run_result(
        group_id="group_10_two_stage_public_recovery",
        batch_id="group_10_two_stage_public_recovery_batch_02",
        timed_out=True,
    )
    summary = build_p7_hold004_backend_suite_execution_summary(run_results=[timeout_result])
    summary["first_timeout"]["present"] = False
    with pytest.raises(ValueError):
        assert_p7_hold004_backend_suite_execution_summary_contract(summary)


def test_r5_execution_summary_contract_rejects_split_green_promotion_or_missing_non_promotion_followup() -> None:
    summary = build_p7_hold004_backend_suite_execution_summary(run_results=_all_green_results_with_one_skip())
    summary["full_backend_suite_green_confirmed"] = True
    with pytest.raises(ValueError):
        assert_p7_hold004_backend_suite_execution_summary_contract(summary)

    summary = build_p7_hold004_backend_suite_execution_summary(run_results=_all_green_results_with_one_skip())
    summary["required_followup_fixes"] = [
        value for value in summary["required_followup_fixes"] if value != "split_green_is_not_full_backend_suite_green"
    ]
    with pytest.raises(ValueError):
        assert_p7_hold004_backend_suite_execution_summary_contract(summary)


def test_r5_execution_summary_records_batches_in_execution_order_not_input_order() -> None:
    group_02_pass = build_p7_hold004_backend_suite_group_run_result(
        group_id="group_02_p7_hold004",
        status=P7_HOLD004_BACKEND_SUITE_STATUS_PASS,
        passed=252,
    )
    group_01_pass = build_p7_hold004_backend_suite_group_run_result(
        group_id="group_01_contract",
        status=P7_HOLD004_BACKEND_SUITE_STATUS_PASS,
        passed=119,
    )
    summary = build_p7_hold004_backend_suite_execution_summary(run_results=[group_01_pass, group_02_pass])

    assert [item["group_id"] for item in summary["recorded_batch_statuses"]] == [
        "group_02_p7_hold004",
        "group_01_contract",
    ]
    assert tuple(summary["recorded_batch_statuses"][0]["group_id"] for _ in [0])[0] == P7_HOLD004_BACKEND_SUITE_EXECUTION_ORDER[0]
    assert_p7_hold004_backend_suite_execution_summary_contract(summary)
