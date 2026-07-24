# -*- coding: utf-8 -*-
from __future__ import annotations

"""Dedicated Step 5 independent-negative proof source for Recovery Epoch 001."""

import importlib

import pytest

import emlis_ai_content_selection_v3 as step5_owner


_STEP = 5
_THIS_PATH = (
    "ai/tests/"
    "test_emlis_nls_v3_recovery_epoch001_step05_independent_negative.py"
)
_NODE_ID = f"{_THIS_PATH}::test_recovery_epoch001_step05_independent_negative"
_RED_CODE = "RECOVERY_EPOCH001_STEP05_DEDICATED_NEGATIVE_NOT_PROVED"
_EXPECTED_PROOF = {
    "source_path": _THIS_PATH,
    "test_node_id": _NODE_ID,
    "validator_path": (
        "ai/services/ai_inference/emlis_ai_content_selection_v3.py"
    ),
    "validator_symbol": "validate_content_selection_policy",
    "attack_id": "INVALID_SEMANTIC_INVENTORY_PARENT",
    "expected_closed_code": "SEMANTIC_INVENTORY_RESULT_TYPE_INVALID",
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


def test_recovery_epoch001_step05_independent_negative() -> None:
    issues = step5_owner.validate_content_selection_policy(
        {},
        inventory_result={},
    )
    assert _EXPECTED_PROOF["expected_closed_code"] in {
        issue.code for issue in issues
    }
    row = _registry_row_or_red()
    assert row.get("independent_negative_proof") == _EXPECTED_PROOF
