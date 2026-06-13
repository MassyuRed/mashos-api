# -*- coding: utf-8 -*-
from __future__ import annotations

import json

import pytest

from emlis_ai_p7_module_inventory import (
    P7_CLASS_HEAVY_E2E_ISOLATED,
    P7_CLASS_RELEASE_DECISION_ISOLATED,
    P7_CLASS_REUSE_DIRECT,
    P7_CLASS_REUSE_WITH_ADAPTER,
    P7_MODULE_INVENTORY_SCHEMA_VERSION,
    assert_p7_module_inventory_contract,
    build_p7_module_inventory,
    build_p7_module_inventory_index,
    get_p7_module_inventory_item,
)

SECRET_INPUT = "P7-2 raw input must never be serialized"
SECRET_COMMENT = "P7-2 comment_text body must never be serialized"


def test_p7_2_module_inventory_classifies_existing_product_quality_modules() -> None:
    inventory = build_p7_module_inventory()
    assert_p7_module_inventory_contract(inventory)

    assert inventory["schema_version"] == P7_MODULE_INVENTORY_SCHEMA_VERSION
    assert inventory["scope"] == "P7_existing_product_quality_module_adapter_classification"
    assert inventory["release_allowed"] is False
    assert inventory["full_backend_suite_green_claim_allowed"] is False
    assert all(value is False for value in inventory["public_contract"].values())
    assert all(value is False for value in inventory["body_free"].values())

    index = build_p7_module_inventory_index(inventory)
    assert index["p5_p6_split_test_matrix_handoff"]["classification"] == P7_CLASS_REUSE_DIRECT
    assert index["product_quality_measurement_event"]["classification"] == P7_CLASS_REUSE_WITH_ADAPTER
    assert index["product_quality_measurement_runner"]["classification"] == P7_CLASS_REUSE_WITH_ADAPTER
    assert index["product_quality_blocker_matrix"]["p7_role"] == "red_ledger_to_blocker_matrix_adapter"
    assert index["runtime_surface_blind_qa_long_run"]["p7_role"] == "ratings_only_material"
    assert index["product_readfeel_long_run_product_gate"]["p7_role"] == "long_run_candidate_material"

    assert inventory["classification_counts"][P7_CLASS_REUSE_DIRECT] == 1
    assert inventory["classification_counts"][P7_CLASS_REUSE_WITH_ADAPTER] >= 5
    assert set(inventory["required_inventory_ids"]).issubset(index)


def test_p7_2_inventory_isolates_release_decision_and_heavy_e2e_from_p7_mainline() -> None:
    inventory = build_p7_module_inventory()
    index = build_p7_module_inventory_index(inventory)

    release_decision = index["product_release_decision"]
    assert release_decision["classification"] == P7_CLASS_RELEASE_DECISION_ISOLATED
    assert release_decision["release_decision_isolated"] is True
    assert release_decision["release_shortcut_risk"] is True
    assert release_decision["runner_mainline_allowed"] is False
    assert release_decision["contract_test_allowed"] is True
    assert release_decision["release_allowed"] is False
    assert "product_release_decision" in inventory["release_decision_isolated_ids"]

    heavy_ids = set(inventory["heavy_e2e_isolated_ids"])
    assert "complete_product_quality_measurement_connection" in heavy_ids
    assert "positive_recovery_e2e_red_source" in heavy_ids
    assert "complete_product_quality_connection_e2e_red_source" in heavy_ids
    for heavy_id in heavy_ids:
        item = index[heavy_id]
        assert item["classification"] == P7_CLASS_HEAVY_E2E_ISOLATED
        assert item["heavy_e2e_isolated"] is True
        assert item["runner_mainline_allowed"] is False
        assert item["timeout_budget_required"] is True
        assert item["linked_red_refs"]

    assert set(inventory["heavy_isolated_red_refs"]) == {"P7-RED-001", "P7-RED-002", "P7-RED-003"}


def test_p7_2_inventory_keeps_body_free_rows_without_completion_or_release_claim() -> None:
    inventory = build_p7_module_inventory()
    dumped = json.dumps(inventory, ensure_ascii=False, sort_keys=True)

    assert SECRET_INPUT not in dumped
    assert SECRET_COMMENT not in dumped
    assert '"raw_input":' not in dumped
    assert '"comment_text":' not in dumped
    assert '"candidate_body":' not in dumped
    assert '"surface_body":' not in dumped
    assert '"release_allowed": true' not in dumped.lower()
    assert '"full_backend_suite_green_claim_allowed": true' not in dumped.lower()

    for item in inventory["items"]:
        assert item["body_free"] is True
        assert item["release_allowed"] is False


def test_p7_2_inventory_lookup_returns_single_body_free_classification() -> None:
    item = get_p7_module_inventory_item("product_quality_measurement_event")

    assert item["path"] == "services/ai_inference/emlis_ai_product_quality_measurement_event.py"
    assert item["adapter_required"] is True
    assert item["runner_bucket"] == "existing_p7_reuse_contract"
    assert item["body_free"] is True

    with pytest.raises(KeyError):
        get_p7_module_inventory_item("missing_module")


def test_p7_2_inventory_contract_rejects_body_payload_release_and_bad_isolation() -> None:
    inventory = build_p7_module_inventory()

    unsafe_release = dict(inventory)
    unsafe_release["release_allowed"] = True
    with pytest.raises(ValueError):
        assert_p7_module_inventory_contract(unsafe_release)

    unsafe_contract = dict(inventory)
    unsafe_contract["public_contract"] = dict(inventory["public_contract"])
    unsafe_contract["public_contract"]["api_response_key_added"] = True
    with pytest.raises(ValueError):
        assert_p7_module_inventory_contract(unsafe_contract)

    unsafe_body = dict(inventory)
    unsafe_body["items"] = list(inventory["items"])
    unsafe_item = dict(unsafe_body["items"][0])
    unsafe_item["comment_text"] = SECRET_COMMENT
    unsafe_body["items"][0] = unsafe_item
    with pytest.raises(ValueError):
        assert_p7_module_inventory_contract(unsafe_body)

    unsafe_heavy = dict(inventory)
    unsafe_heavy["items"] = [dict(item) for item in inventory["items"]]
    for item in unsafe_heavy["items"]:
        if item["id"] == "complete_product_quality_connection_e2e_red_source":
            item["runner_mainline_allowed"] = True
            break
    with pytest.raises(ValueError):
        assert_p7_module_inventory_contract(unsafe_heavy)
