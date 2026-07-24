# -*- coding: utf-8 -*-
from __future__ import annotations

"""Dedicated Step 8 independent-negative proof source for Recovery Epoch 001."""

import importlib

import pytest

import emlis_ai_body_semantic_atom_parser_v3 as step8_owner


_STEP = 8
_THIS_PATH = (
    "ai/tests/"
    "test_emlis_nls_v3_recovery_epoch001_step08_independent_negative.py"
)
_NODE_ID = f"{_THIS_PATH}::test_recovery_epoch001_step08_independent_negative"
_RED_CODE = "RECOVERY_EPOCH001_STEP08_DEDICATED_NEGATIVE_NOT_PROVED"
_EXPECTED_PROOF = {
    "source_path": _THIS_PATH,
    "test_node_id": _NODE_ID,
    "validator_path": (
        "ai/services/ai_inference/"
        "emlis_ai_body_semantic_atom_parser_v3.py"
    ),
    "validator_symbol": "parse_body_semantic_atoms",
    "attack_id": "NON_UTF8_CANDIDATE_BYTES",
    "expected_closed_code": "CANDIDATE_UTF8_REQUIRED",
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


def test_recovery_epoch001_step08_independent_negative() -> None:
    with pytest.raises(
        step8_owner.BodySemanticAtomParseError,
        match=_EXPECTED_PROOF["expected_closed_code"],
    ):
        step8_owner.parse_body_semantic_atoms(b"\xff")
    row = _registry_row_or_red()
    assert row.get("independent_negative_proof") == _EXPECTED_PROOF
