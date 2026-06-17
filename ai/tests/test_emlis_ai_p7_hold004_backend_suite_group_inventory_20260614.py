# -*- coding: utf-8 -*-
"""R15 contract tests for P7-HOLD-004 current backend-suite group inventory material."""

from __future__ import annotations

import json

import pytest

from emlis_ai_p7_contracts import assert_p7_no_body_payload_or_contract_mutation
from emlis_ai_p7_hold004_backend_suite_group_inventory_plan import (
    P7_HOLD004_BACKEND_COLLECT_STATUS_COLLECTION_FAILED,
    P7_HOLD004_BACKEND_R2_R3_SOURCE_SNAPSHOT_REF,
    P7_HOLD004_BACKEND_SUITE_GROUP_IDS,
    P7_HOLD004_BACKEND_SUITE_GROUP_INVENTORY_ID,
    P7_HOLD004_BACKEND_SUITE_GROUP_INVENTORY_SCHEMA_VERSION,
    P7_HOLD004_BACKEND_SUITE_GROUPING_RULE_VERSION,
    P7_HOLD004_BACKEND_SUITE_SPLIT_CONSISTENCY_R2_R3_STEP,
    P7_HOLD004_BACKEND_SUITE_TOTAL_GROUP_FILE_COUNT,
    P7_HOLD004_BACKEND_SUITE_TOTAL_GROUP_TEST_ITEM_COUNT,
    assert_p7_hold004_backend_suite_group_inventory_contract,
    build_p7_hold004_backend_suite_group_inventory,
    classify_p7_hold004_backend_test_file_ref,
)
from emlis_ai_p7_hold004_backend_suite_split_consistency import (
    P7_HOLD004_BACKEND_COLLECTED_TEST_FILE_COUNT,
    P7_HOLD004_BACKEND_COLLECTED_TEST_ITEM_COUNT,
    build_p7_hold004_backend_collect_baseline,
)

_SAMPLE_COMMENT_BODY = "これはP7 materialに入れてはいけないcomment_text本文です"
_SAMPLE_TERMINAL_OUTPUT = "FAILED tests/example.py::test_x -- traceback body"


def _group_by_id(inventory: dict[str, object], group_id: str) -> dict[str, object]:
    for group in inventory["groups"]:  # type: ignore[index]
        if group["group_id"] == group_id:
            return group
    raise AssertionError(f"missing group: {group_id}")


def test_r15_group_inventory_material_uses_current_collect_baseline_without_green_or_release_promotion() -> None:
    inventory = build_p7_hold004_backend_suite_group_inventory()

    assert inventory["schema_version"] == P7_HOLD004_BACKEND_SUITE_GROUP_INVENTORY_SCHEMA_VERSION
    assert inventory["phase"] == "P7_ProductQualityRunner_LongRunGate"
    assert inventory["step"] == P7_HOLD004_BACKEND_SUITE_SPLIT_CONSISTENCY_R2_R3_STEP
    assert inventory["implementation_step"] == P7_HOLD004_BACKEND_SUITE_SPLIT_CONSISTENCY_R2_R3_STEP
    assert inventory["hold_id"] == "P7-HOLD-004"
    assert inventory["inventory_id"] == P7_HOLD004_BACKEND_SUITE_GROUP_INVENTORY_ID
    assert inventory["collect_baseline_id"] == "p7_hold004_backend_collect_baseline_20260615_received_148"
    assert inventory["source_mode"] == "local_snapshot"
    assert inventory["source_snapshot_ref"] == P7_HOLD004_BACKEND_R2_R3_SOURCE_SNAPSHOT_REF
    assert inventory["git_checked"] is False
    assert inventory["grouping_rule_version"] == P7_HOLD004_BACKEND_SUITE_GROUPING_RULE_VERSION
    assert inventory["group_count"] == 13
    assert inventory["total_group_file_count"] == P7_HOLD004_BACKEND_SUITE_TOTAL_GROUP_FILE_COUNT == 425
    assert inventory["total_group_test_item_count"] == P7_HOLD004_BACKEND_SUITE_TOTAL_GROUP_TEST_ITEM_COUNT == 2856
    assert inventory["collected_test_file_count"] == P7_HOLD004_BACKEND_COLLECTED_TEST_FILE_COUNT == 425
    assert inventory["collected_test_item_count"] == P7_HOLD004_BACKEND_COLLECTED_TEST_ITEM_COUNT == 2856
    assert inventory["unassigned_test_file_count"] == 0
    assert inventory["duplicate_assignment_count"] == 0

    assert [group["group_id"] for group in inventory["groups"]] == list(P7_HOLD004_BACKEND_SUITE_GROUP_IDS)
    assert len(inventory["assignment_rules"]) == 13
    assert [rule["group_id"] for rule in inventory["assignment_rules"]] == list(P7_HOLD004_BACKEND_SUITE_GROUP_IDS)

    assert _group_by_id(inventory, "group_01_contract")["file_count"] == 18
    assert _group_by_id(inventory, "group_02_p7_hold004")["file_count"] == 19
    assert _group_by_id(inventory, "group_02_p7_hold004")["test_item_count"] == 252
    assert _group_by_id(inventory, "group_11_emlis_runtime_other")["file_count"] == 201
    assert _group_by_id(inventory, "group_11_emlis_runtime_other")["planned_batch_count"] == 6
    assert _group_by_id(inventory, "group_11_emlis_runtime_other")["batch_policy"] == "required_batch_by_30_files_or_250_tests"

    assert inventory["full_backend_suite_green_confirmed"] is False
    assert inventory["full_backend_suite_green_claim_allowed"] is False
    assert inventory["split_green_is_full_backend_suite_green"] is False
    assert inventory["split_green_can_close_p7_hold004"] is False
    assert inventory["hold004_close_allowed"] is False
    assert inventory["p7_complete"] is False
    assert inventory["p8_start_allowed"] is False
    assert inventory["release_allowed"] is False
    assert "P7-HOLD-004" in inventory["unresolved_hold_refs"]
    assert "full_backend_suite_green_unconfirmed" in inventory["required_followup_fixes"]
    assert all(value is False for value in inventory["public_contract"].values())
    assert all(value is False for value in inventory["body_free_markers"].values())
    assert inventory["body_free"] is True
    assert inventory["current_collect_baseline_reconciled"] is True
    assert inventory["previous_baseline_is_not_current"] is True
    assert inventory["baseline_mismatch_blocks_execution"] is True
    assert all(group["can_claim_full_backend_suite_green"] is False for group in inventory["groups"])
    assert all(group["release_allowed"] is False for group in inventory["groups"])
    assert all(group["body_free"] is True for group in inventory["groups"])

    serialized = json.dumps(inventory, ensure_ascii=False, sort_keys=True)
    assert _SAMPLE_COMMENT_BODY not in serialized
    assert _SAMPLE_TERMINAL_OUTPUT not in serialized
    assert "terminal_output" not in inventory
    assert "stdout" not in inventory
    assert "stderr" not in inventory
    assert "traceback" not in inventory

    assert_p7_hold004_backend_suite_group_inventory_contract(inventory)
    assert_p7_no_body_payload_or_contract_mutation(inventory, source="r2_backend_group_inventory_test")


@pytest.mark.parametrize(
    ("file_ref", "expected_group_id"),
    (
        ("tests/contract/test_emlis_ai_contracts.py", "group_01_contract"),
        ("tests/test_emlis_ai_p7_hold004_positive_public_shape_boundary_20260614.py", "group_02_p7_hold004"),
        ("tests/test_emlis_ai_p7_release_handoff_20260612.py", "group_03_p7_core_matrix_handoff"),
        ("tests/test_emlis_ai_complete_product_quality_connection_e2e.py", "group_04_complete_product_quality"),
        ("tests/test_emlis_ai_user_label_connection_surface.py", "group_05_user_label_connection_p5"),
        ("tests/test_emlis_ai_structure_insight_gate.py", "group_06_structure_insight_p6"),
        ("tests/test_emlis_ai_product_quality_runner.py", "group_07_product_quality_legacy_runner"),
        ("tests/test_emlis_ai_complete_initial_surface_recomposition_p5.py", "group_08_complete_initial"),
        ("tests/test_emlis_ai_complete_phase16_composer.py", "group_09_complete_composer_other"),
        ("tests/test_emotion_submit_two_stage_reception_e2e.py", "group_10_two_stage_public_recovery"),
        ("tests/test_emlis_ai_runtime_candidate_gate.py", "group_11_emlis_runtime_other"),
        ("tests/test_subscription_boundary.py", "group_12_analysis_subscription_piece_self_structure"),
        ("tests/test_other_backend_contract.py", "group_13_remaining_backend_other"),
    ),
)
def test_r15_group_classifier_keeps_ordered_inventory_rules(file_ref: str, expected_group_id: str) -> None:
    assert classify_p7_hold004_backend_test_file_ref(file_ref) == expected_group_id


def test_r15_group_inventory_rejects_non_collected_baseline() -> None:
    failed_baseline = build_p7_hold004_backend_collect_baseline(
        collection_status=P7_HOLD004_BACKEND_COLLECT_STATUS_COLLECTION_FAILED
    )

    with pytest.raises(ValueError):
        build_p7_hold004_backend_suite_group_inventory(collect_baseline=failed_baseline)


@pytest.mark.parametrize(
    ("field", "bad_value"),
    (
        ("group_count", 12),
        ("total_group_file_count", 424),
        ("total_group_test_item_count", 2855),
        ("unassigned_test_file_count", 1),
        ("duplicate_assignment_count", 1),
        ("full_backend_suite_green_confirmed", True),
        ("split_green_is_full_backend_suite_green", True),
        ("split_green_can_close_p7_hold004", True),
        ("hold004_close_allowed", True),
        ("p7_complete", True),
        ("p8_start_allowed", True),
        ("release_allowed", True),
    ),
)
def test_r15_group_inventory_contract_rejects_count_assignment_or_release_mutation(field: str, bad_value: object) -> None:
    inventory = build_p7_hold004_backend_suite_group_inventory()
    inventory[field] = bad_value

    with pytest.raises(ValueError):
        assert_p7_hold004_backend_suite_group_inventory_contract(inventory)


def test_r15_group_inventory_contract_rejects_group_level_green_release_or_count_mutation() -> None:
    inventory = build_p7_hold004_backend_suite_group_inventory()
    _group_by_id(inventory, "group_11_emlis_runtime_other")["can_claim_full_backend_suite_green"] = True
    with pytest.raises(ValueError):
        assert_p7_hold004_backend_suite_group_inventory_contract(inventory)

    inventory = build_p7_hold004_backend_suite_group_inventory()
    _group_by_id(inventory, "group_11_emlis_runtime_other")["release_allowed"] = True
    with pytest.raises(ValueError):
        assert_p7_hold004_backend_suite_group_inventory_contract(inventory)

    inventory = build_p7_hold004_backend_suite_group_inventory()
    _group_by_id(inventory, "group_11_emlis_runtime_other")["file_count"] = 200
    with pytest.raises(ValueError):
        assert_p7_hold004_backend_suite_group_inventory_contract(inventory)

    for flag in (
        "current_collect_baseline_reconciled",
        "previous_baseline_is_not_current",
        "baseline_mismatch_blocks_execution",
    ):
        inventory = build_p7_hold004_backend_suite_group_inventory()
        inventory[flag] = False
        with pytest.raises(ValueError):
            assert_p7_hold004_backend_suite_group_inventory_contract(inventory)


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
def test_r15_group_inventory_contract_rejects_body_free_marker_or_body_payload(marker_key: str) -> None:
    inventory = build_p7_hold004_backend_suite_group_inventory()
    inventory["body_free_markers"][marker_key] = True
    with pytest.raises(ValueError):
        assert_p7_hold004_backend_suite_group_inventory_contract(inventory)

    inventory = build_p7_hold004_backend_suite_group_inventory()
    inventory["terminal_output"] = _SAMPLE_TERMINAL_OUTPUT
    with pytest.raises(ValueError):
        assert_p7_hold004_backend_suite_group_inventory_contract(inventory)
