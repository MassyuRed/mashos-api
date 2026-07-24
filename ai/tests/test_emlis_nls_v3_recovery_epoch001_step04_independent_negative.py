# -*- coding: utf-8 -*-
from __future__ import annotations

"""Dedicated Step 4 independent-negative proof source for Recovery Epoch 001."""

import importlib

import pytest

import emlis_ai_semantic_obligation_inventory_v3 as step4_owner


_STEP = 4
_THIS_PATH = (
    "ai/tests/"
    "test_emlis_nls_v3_recovery_epoch001_step04_independent_negative.py"
)
_NODE_ID = f"{_THIS_PATH}::test_recovery_epoch001_step04_independent_negative"
_RED_CODE = "RECOVERY_EPOCH001_STEP04_DEDICATED_NEGATIVE_NOT_PROVED"
_EXPECTED_PROOF = {
    "source_path": _THIS_PATH,
    "test_node_id": _NODE_ID,
    "validator_path": (
        "ai/services/ai_inference/"
        "emlis_ai_semantic_obligation_inventory_v3.py"
    ),
    "validator_symbol": "validate_obligation_inventory_count",
    "attack_id": "BOUND_PLUS_ONE_OBLIGATION_COUNT",
    "expected_closed_code": "OBLIGATION_INVENTORY_OVERFLOW",
}


def _registry_row_or_red() -> dict[str, object]:
    try:
        module = importlib.import_module(
            "emlis_ai_recovery_epoch001_current_step_requirement_registry_v3"
        )
    except ModuleNotFoundError as exc:
        if exc.name == (
            "emlis_ai_recovery_epoch001_current_step_requirement_registry_v3"
        ):
            pytest.fail(_RED_CODE, pytrace=False)
        raise
    builder = getattr(
        module,
        "fresh_recovery_epoch001_current_step_requirement_registry",
        None,
    )
    if not callable(builder):
        pytest.fail(_RED_CODE, pytrace=False)
    registry = builder()
    rows = registry.get("steps") if type(registry) is dict else None
    if type(rows) is not list:
        pytest.fail(_RED_CODE, pytrace=False)
    row = next(
        (
            item
            for item in rows
            if type(item) is dict and item.get("step_number") == _STEP
        ),
        None,
    )
    if type(row) is not dict:
        pytest.fail(_RED_CODE, pytrace=False)
    return row


def test_recovery_epoch001_step04_independent_negative() -> None:
    source_counts = {
        "evidence_span_count": 1,
        "text_evidence_span_count": 1,
        "nucleus_count": 1,
        "relation_count": 0,
        "unknown_boundary_count": 0,
        "safety_policy_count": 1,
        "safety_required_boundary_code_count": 0,
        "reception_opportunity_count": 1,
    }
    issues = step4_owner.validate_obligation_inventory_count(
        source_counts,
        25,
    )
    assert _EXPECTED_PROOF["expected_closed_code"] in issues
    row = _registry_row_or_red()
    assert row.get("independent_negative_proof") == _EXPECTED_PROOF
