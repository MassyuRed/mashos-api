# -*- coding: utf-8 -*-
"""P7-2 existing Product Quality module inventory and adapter classification.

The inventory is intentionally body-free and release-closed.  Existing Product
Quality modules are not treated as proof that P7 is complete; each module/test is
classified by its role after the P5/P6 body-free handoff.  Heavy E2E sources and
release-decision surfaces are isolated from the P7 runner mainline.
"""

from __future__ import annotations

from collections import Counter
from collections.abc import Mapping, Sequence
from typing import Any, Final

from emlis_ai_p7_contracts import (
    P7_PHASE,
    assert_false_markers,
    assert_p7_no_body_payload_or_contract_mutation,
    body_free_flags,
    clean_identifier,
    dedupe_identifiers,
    public_contract_flags,
    safe_mapping,
)

P7_MODULE_INVENTORY_SCHEMA_VERSION: Final = "cocolon.emlis.p7.module_inventory.v1"
P7_MODULE_INVENTORY_SCOPE: Final = "P7_existing_product_quality_module_adapter_classification"
P7_MODULE_INVENTORY_STEP: Final = "P7-2_ModuleInventoryAdapterClassification_20260612"

P7_CLASS_REUSE_DIRECT: Final = "reuse_direct"
P7_CLASS_REUSE_WITH_ADAPTER: Final = "reuse_with_adapter"
P7_CLASS_HEAVY_E2E_ISOLATED: Final = "heavy_e2e_isolated"
P7_CLASS_RELEASE_DECISION_ISOLATED: Final = "release_decision_isolated"
P7_CLASS_OUT_OF_SCOPE: Final = "out_of_scope"

P7_MODULE_CLASSIFICATIONS: Final[tuple[str, ...]] = (
    P7_CLASS_REUSE_DIRECT,
    P7_CLASS_REUSE_WITH_ADAPTER,
    P7_CLASS_HEAVY_E2E_ISOLATED,
    P7_CLASS_RELEASE_DECISION_ISOLATED,
    P7_CLASS_OUT_OF_SCOPE,
)

_REQUIRED_INVENTORY_IDS: Final[tuple[str, ...]] = (
    "p5_p6_split_test_matrix_handoff",
    "product_quality_measurement_event",
    "product_quality_measurement_runner",
    "product_quality_blocker_matrix",
    "runtime_surface_blind_qa_long_run",
    "product_readfeel_long_run_product_gate",
    "product_release_decision",
    "complete_product_quality_measurement_connection",
    "positive_recovery_e2e_red_source",
    "complete_product_quality_connection_e2e_red_source",
)

_ALLOWED_ITEM_KINDS: Final[frozenset[str]] = frozenset({"module", "test"})
_ALLOWED_RUNNER_BUCKETS: Final[frozenset[str]] = frozenset(
    {
        "p7_core_contract",
        "existing_p7_reuse_contract",
        "heavy_isolated_red",
        "release_decision_handoff",
        "out_of_scope",
    }
)
_ALLOWED_P7_ROLES: Final[frozenset[str]] = frozenset(
    {
        "handoff_input_material",
        "body_free_event_source",
        "runner_candidate_with_adapter",
        "red_ledger_to_blocker_matrix_adapter",
        "ratings_only_material",
        "long_run_candidate_material",
        "release_decision_handoff_only",
        "heavy_connection_isolated_source",
        "red_source_only",
        "scope_boundary",
    }
)


def _inventory_item(
    item_id: str,
    *,
    kind: str,
    path: str,
    classification: str,
    p7_role: str,
    runner_bucket: str,
    adapter_required: bool,
    runner_mainline_allowed: bool,
    contract_test_allowed: bool,
    release_decision_isolated: bool = False,
    release_shortcut_risk: bool = False,
    heavy_e2e_isolated: bool = False,
    timeout_budget_required: bool = False,
    linked_red_refs: Sequence[str] = (),
    linked_hold_refs: Sequence[str] = (),
    notes: Sequence[str] = (),
) -> dict[str, Any]:
    return {
        "id": clean_identifier(item_id, max_length=120),
        "kind": clean_identifier(kind, max_length=32),
        "path": clean_identifier(path, max_length=220),
        "classification": clean_identifier(classification, max_length=64),
        "p7_role": clean_identifier(p7_role, max_length=80),
        "runner_bucket": clean_identifier(runner_bucket, max_length=80),
        "adapter_required": adapter_required is True,
        "runner_mainline_allowed": runner_mainline_allowed is True,
        "contract_test_allowed": contract_test_allowed is True,
        "release_decision_isolated": release_decision_isolated is True,
        "release_shortcut_risk": release_shortcut_risk is True,
        "heavy_e2e_isolated": heavy_e2e_isolated is True,
        "timeout_budget_required": timeout_budget_required is True,
        "linked_red_refs": dedupe_identifiers(linked_red_refs, limit=8),
        "linked_hold_refs": dedupe_identifiers(linked_hold_refs, limit=8),
        "notes": dedupe_identifiers(notes, limit=8, max_length=180),
        "body_free": True,
        "release_allowed": False,
    }


def _initial_inventory_items() -> list[dict[str, Any]]:
    """Return the fixed P7-2 inventory rows without reading or storing bodies."""

    return [
        _inventory_item(
            "p5_p6_split_test_matrix_handoff",
            kind="module",
            path="services/ai_inference/emlis_ai_p5_p6_split_test_matrix.py",
            classification=P7_CLASS_REUSE_DIRECT,
            p7_role="handoff_input_material",
            runner_bucket="existing_p7_reuse_contract",
            adapter_required=False,
            runner_mainline_allowed=True,
            contract_test_allowed=True,
            linked_hold_refs=("P7-HOLD-001", "P7-HOLD-002"),
            notes=(
                "Read as a safe P5/P6-to-P7 intake material, not as P7 completion evidence.",
                "P7 ready and release_allowed remain false after this handoff.",
            ),
        ),
        _inventory_item(
            "product_quality_measurement_event",
            kind="module",
            path="services/ai_inference/emlis_ai_product_quality_measurement_event.py",
            classification=P7_CLASS_REUSE_WITH_ADAPTER,
            p7_role="body_free_event_source",
            runner_bucket="existing_p7_reuse_contract",
            adapter_required=True,
            runner_mainline_allowed=True,
            contract_test_allowed=True,
            notes=(
                "Reuse ProductQualityEventV1 as a lower-level row source.",
                "Keep the P7 handoff summary and scorecard bridge separated.",
            ),
        ),
        _inventory_item(
            "product_quality_measurement_runner",
            kind="module",
            path="services/ai_inference/emlis_ai_product_quality_measurement_runner.py",
            classification=P7_CLASS_REUSE_WITH_ADAPTER,
            p7_role="runner_candidate_with_adapter",
            runner_bucket="existing_p7_reuse_contract",
            adapter_required=True,
            runner_mainline_allowed=True,
            contract_test_allowed=True,
            notes=(
                "Reuse only through the P7 handoff adapter and split command plan.",
                "Do not promote fixture green to Product Pass or release readiness.",
            ),
        ),
        _inventory_item(
            "product_quality_blocker_matrix",
            kind="module",
            path="services/ai_inference/emlis_ai_product_quality_blocker_matrix.py",
            classification=P7_CLASS_REUSE_WITH_ADAPTER,
            p7_role="red_ledger_to_blocker_matrix_adapter",
            runner_bucket="existing_p7_reuse_contract",
            adapter_required=True,
            runner_mainline_allowed=True,
            contract_test_allowed=True,
            linked_red_refs=("P7-RED-001", "P7-RED-002"),
            notes=(
                "Accepts P7 red ledger adapter candidates.",
                "Does not close Positive Recovery reds as old tests.",
            ),
        ),
        _inventory_item(
            "runtime_surface_blind_qa_long_run",
            kind="module",
            path="services/ai_inference/emlis_ai_runtime_surface_blind_qa_long_run.py",
            classification=P7_CLASS_REUSE_WITH_ADAPTER,
            p7_role="ratings_only_material",
            runner_bucket="existing_p7_reuse_contract",
            adapter_required=True,
            runner_mainline_allowed=True,
            contract_test_allowed=True,
            linked_hold_refs=("P7-HOLD-001", "P7-HOLD-003"),
            notes=(
                "Reuse for ratings-only material export.",
                "Human QA missing dimensions remain HOLD, never machine-filled.",
            ),
        ),
        _inventory_item(
            "product_readfeel_long_run_product_gate",
            kind="module",
            path="services/ai_inference/emlis_ai_product_readfeel_long_run_product_gate.py",
            classification=P7_CLASS_REUSE_WITH_ADAPTER,
            p7_role="long_run_candidate_material",
            runner_bucket="existing_p7_reuse_contract",
            adapter_required=True,
            runner_mainline_allowed=True,
            contract_test_allowed=True,
            release_shortcut_risk=True,
            linked_hold_refs=("P7-HOLD-001", "P7-HOLD-002"),
            notes=(
                "Use as long-run candidate material only.",
                "Product Pass candidates are not converted to Release Ready in P7.",
            ),
        ),
        _inventory_item(
            "product_release_decision",
            kind="module",
            path="services/ai_inference/emlis_ai_product_release_decision.py",
            classification=P7_CLASS_RELEASE_DECISION_ISOLATED,
            p7_role="release_decision_handoff_only",
            runner_bucket="release_decision_handoff",
            adapter_required=True,
            runner_mainline_allowed=False,
            contract_test_allowed=True,
            release_decision_isolated=True,
            release_shortcut_risk=True,
            linked_red_refs=("P7-RED-001", "P7-RED-002", "P7-RED-003"),
            linked_hold_refs=("P7-HOLD-004",),
            notes=(
                "Keep outside the P7 mainline as a handoff target.",
                "P7 must not emit release_allowed true.",
            ),
        ),
        _inventory_item(
            "complete_product_quality_measurement_connection",
            kind="module",
            path="services/ai_inference/emlis_ai_complete_product_quality_measurement_connection.py",
            classification=P7_CLASS_HEAVY_E2E_ISOLATED,
            p7_role="heavy_connection_isolated_source",
            runner_bucket="heavy_isolated_red",
            adapter_required=True,
            runner_mainline_allowed=False,
            contract_test_allowed=False,
            heavy_e2e_isolated=True,
            timeout_budget_required=True,
            linked_red_refs=("P7-RED-003",),
            notes=(
                "Keep the complete Product Quality connection out of the P7 core runner.",
                "Timeout or hang remains ledgered instead of green.",
            ),
        ),
        _inventory_item(
            "positive_recovery_e2e_red_source",
            kind="test",
            path="tests/test_emlis_ai_complete_product_quality_positive_recovery_e2e.py",
            classification=P7_CLASS_HEAVY_E2E_ISOLATED,
            p7_role="red_source_only",
            runner_bucket="heavy_isolated_red",
            adapter_required=False,
            runner_mainline_allowed=False,
            contract_test_allowed=False,
            heavy_e2e_isolated=True,
            timeout_budget_required=True,
            linked_red_refs=("P7-RED-001", "P7-RED-002"),
            notes=(
                "Preserve Positive Recovery failures as P7 red sources.",
                "Do not treat relation mismatch or fail-closed regression as stale expectations.",
            ),
        ),
        _inventory_item(
            "complete_product_quality_connection_e2e_red_source",
            kind="test",
            path="tests/test_emlis_ai_complete_product_quality_connection_e2e.py",
            classification=P7_CLASS_HEAVY_E2E_ISOLATED,
            p7_role="red_source_only",
            runner_bucket="heavy_isolated_red",
            adapter_required=False,
            runner_mainline_allowed=False,
            contract_test_allowed=False,
            heavy_e2e_isolated=True,
            timeout_budget_required=True,
            linked_red_refs=("P7-RED-003",),
            notes=(
                "Preserve heavy Product Quality Connection timeout as P7-RED-003.",
                "Do not run in the P7 core pass command.",
            ),
        ),
    ]


def build_p7_module_inventory() -> dict[str, Any]:
    """Build the body-free P7-2 module inventory."""

    items = _initial_inventory_items()
    counts = Counter(item["classification"] for item in items)
    inventory = {
        "schema_version": P7_MODULE_INVENTORY_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_MODULE_INVENTORY_STEP,
        "scope": P7_MODULE_INVENTORY_SCOPE,
        "items": items,
        "classification_counts": {classification: counts.get(classification, 0) for classification in P7_MODULE_CLASSIFICATIONS},
        "required_inventory_ids": list(_REQUIRED_INVENTORY_IDS),
        "release_decision_isolated_ids": [item["id"] for item in items if item["release_decision_isolated"]],
        "heavy_e2e_isolated_ids": [item["id"] for item in items if item["heavy_e2e_isolated"]],
        "runner_mainline_allowed_ids": [item["id"] for item in items if item["runner_mainline_allowed"]],
        "contract_test_allowed_ids": [item["id"] for item in items if item["contract_test_allowed"]],
        "heavy_isolated_red_refs": sorted(
            {red_ref for item in items if item["heavy_e2e_isolated"] for red_ref in item["linked_red_refs"]}
        ),
        "public_contract": public_contract_flags(),
        "body_free": body_free_flags(include_history=False, include_reviewer=True),
        "full_backend_suite_green_claim_allowed": False,
        "release_allowed": False,
    }
    assert_p7_module_inventory_contract(inventory)
    return inventory


def build_p7_module_inventory_index(inventory: Mapping[str, Any] | None = None) -> dict[str, dict[str, Any]]:
    """Return an id-indexed view of the P7-2 inventory."""

    data = safe_mapping(inventory) if inventory is not None else build_p7_module_inventory()
    assert_p7_module_inventory_contract(data)
    return {str(item["id"]): safe_mapping(item) for item in data["items"]}


def get_p7_module_inventory_item(item_id: str, inventory: Mapping[str, Any] | None = None) -> dict[str, Any]:
    index = build_p7_module_inventory_index(inventory)
    key = clean_identifier(item_id)
    if key not in index:
        raise KeyError(key)
    return dict(index[key])


def assert_p7_module_inventory_contract(inventory: Mapping[str, Any]) -> bool:
    data = safe_mapping(inventory)
    if data.get("schema_version") != P7_MODULE_INVENTORY_SCHEMA_VERSION:
        raise ValueError("unexpected P7 module inventory schema_version")
    if data.get("phase") != P7_PHASE:
        raise ValueError("unexpected P7 module inventory phase")
    if data.get("scope") != P7_MODULE_INVENTORY_SCOPE:
        raise ValueError("unexpected P7 module inventory scope")
    if data.get("release_allowed") is not False:
        raise ValueError("P7 module inventory must not allow release")
    if data.get("full_backend_suite_green_claim_allowed") is not False:
        raise ValueError("P7 module inventory must not claim full backend suite green")
    assert_false_markers(safe_mapping(data.get("public_contract")), source="p7_module_inventory.public_contract")
    assert_false_markers(safe_mapping(data.get("body_free")), source="p7_module_inventory.body_free")
    assert_p7_no_body_payload_or_contract_mutation(data, source="p7_module_inventory")

    items = data.get("items")
    if not isinstance(items, list) or not items:
        raise ValueError("P7 module inventory must contain items")
    seen: set[str] = set()
    for raw_item in items:
        item = safe_mapping(raw_item)
        item_id = clean_identifier(item.get("id"))
        if not item_id or item_id in seen:
            raise ValueError("P7 module inventory items must have unique ids")
        seen.add(item_id)
        if clean_identifier(item.get("kind")) not in _ALLOWED_ITEM_KINDS:
            raise ValueError(f"P7 module inventory item has invalid kind: {item_id}")
        if clean_identifier(item.get("classification")) not in P7_MODULE_CLASSIFICATIONS:
            raise ValueError(f"P7 module inventory item has invalid classification: {item_id}")
        if clean_identifier(item.get("runner_bucket")) not in _ALLOWED_RUNNER_BUCKETS:
            raise ValueError(f"P7 module inventory item has invalid runner bucket: {item_id}")
        if clean_identifier(item.get("p7_role")) not in _ALLOWED_P7_ROLES:
            raise ValueError(f"P7 module inventory item has invalid P7 role: {item_id}")
        if item.get("body_free") is not True:
            raise ValueError(f"P7 module inventory item must be body-free: {item_id}")
        if item.get("release_allowed") is not False:
            raise ValueError(f"P7 module inventory item must remain release-closed: {item_id}")
        if item.get("classification") == P7_CLASS_RELEASE_DECISION_ISOLATED and item.get("release_decision_isolated") is not True:
            raise ValueError(f"release decision item must be isolated: {item_id}")
        if item.get("classification") == P7_CLASS_HEAVY_E2E_ISOLATED:
            if item.get("heavy_e2e_isolated") is not True:
                raise ValueError(f"heavy E2E item must be isolated: {item_id}")
            if item.get("runner_mainline_allowed") is not False:
                raise ValueError(f"heavy E2E item must not be in runner mainline: {item_id}")
            if not item.get("linked_red_refs"):
                raise ValueError(f"heavy E2E item must keep red refs: {item_id}")
    missing = set(_REQUIRED_INVENTORY_IDS) - seen
    if missing:
        raise ValueError(f"P7 module inventory missing required ids: {sorted(missing)}")
    if "product_release_decision" not in data.get("release_decision_isolated_ids", []):
        raise ValueError("product release decision must be isolated from P7 mainline")
    if "complete_product_quality_connection_e2e_red_source" not in data.get("heavy_e2e_isolated_ids", []):
        raise ValueError("complete Product Quality Connection E2E must be heavy-isolated")
    return True
