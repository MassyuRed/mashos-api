# -*- coding: utf-8 -*-
from __future__ import annotations

"""Dedicated Step 6 independent-negative proof source for Recovery Epoch 001."""

import importlib

import pytest

import emlis_ai_discourse_graph_planner_v3 as step6_owner


_STEP = 6
_THIS_PATH = (
    "ai/tests/"
    "test_emlis_nls_v3_recovery_epoch001_step06_independent_negative.py"
)
_NODE_ID = f"{_THIS_PATH}::test_recovery_epoch001_step06_independent_negative"
_RED_CODE = "RECOVERY_EPOCH001_STEP06_DEDICATED_NEGATIVE_NOT_PROVED"
_EXPECTED_PROOF = {
    "source_path": _THIS_PATH,
    "test_node_id": _NODE_ID,
    "validator_path": (
        "ai/services/ai_inference/emlis_ai_discourse_graph_planner_v3.py"
    ),
    "validator_symbol": "validate_discourse_graph_plan_set",
    "attack_id": "INVALID_DISCOURSE_PARENT_CHAIN",
    "expected_closed_code": "DISCOURSE_PARENT_REVALIDATION_FAILED",
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


def test_recovery_epoch001_step06_independent_negative() -> None:
    issues = step6_owner.validate_discourse_graph_plan_set(
        {},
        inventory_result={},
        content_plan={},
    )
    assert _EXPECTED_PROOF["expected_closed_code"] in issues
    row = _registry_row_or_red()
    assert row.get("independent_negative_proof") == _EXPECTED_PROOF
