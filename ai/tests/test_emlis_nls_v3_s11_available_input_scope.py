# -*- coding: utf-8 -*-
from __future__ import annotations

"""Frozen Step 11 auxiliary-input scope and zero-source attestation tests."""

from copy import deepcopy
from pathlib import Path
import sys

import pytest


_HERE = Path(__file__).resolve().parent
_AI_ROOT = _HERE.parent
_TOOLS = _AI_ROOT / "tools"
if str(_TOOLS) not in sys.path:
    sys.path.insert(0, str(_TOOLS))

from emlis_ai_step10_evidence_v3 import assert_body_free  # noqa: E402
from emlis_ai_step11_cycle_evidence_v3 import (  # noqa: E402
    STEP11_CURRENT_CANDIDATE_VERSION_ID,
)
from emlis_nls_v3_s0_s1_baseline import load_json  # noqa: E402
from emlis_nls_v3_s2_sample_registry import (  # noqa: E402
    REGISTRY_PATH,
    STEP1_INPUT_CONTRACT_PATH,
    STEP1_RECEIPT_PATH,
)
from emlis_nls_v3_step11_cycle_finalize import (  # noqa: E402
    AVAILABLE_INPUT_SCOPE_RECEIPT_SCHEMA,
    build_available_input_scope_receipt,
    validate_available_input_scope_receipt,
)


def _parents() -> dict[str, object]:
    return {
        "step1_baseline_receipt": load_json(STEP1_RECEIPT_PATH),
        "step1_input_contract": load_json(STEP1_INPUT_CONTRACT_PATH),
        "step2_corpus_registry": load_json(REGISTRY_PATH),
    }


def test_s11_available_input_scope_is_frozen_complete_and_body_free() -> None:
    parents = _parents()
    receipt = build_available_input_scope_receipt(**parents)

    assert receipt["schema_version"] == AVAILABLE_INPUT_SCOPE_RECEIPT_SCHEMA
    assert receipt["candidate_version_id"] == (
        STEP11_CURRENT_CANDIDATE_VERSION_ID
    )
    assert receipt["formal_status"] == "scope_frozen"
    assert receipt["body_free"] is True
    assert validate_available_input_scope_receipt(receipt, **parents) == ()
    assert_body_free(receipt)

    aggregate = receipt["scope_aggregate"]
    assert aggregate == {
        "known_inventory_entry_count": 11,
        "known_machine_execution_cohort_count": 2,
        "known_machine_execution_case_count": 70,
        "legacy_registered_case_count": 3,
        "legacy_app_reachable_to_execute_count": 0,
        "legacy_expected_non_applicable_count": 3,
        "legacy_contract_negative_expected_rejection_count": 0,
        "available_real_user_current_valid_count": 0,
        "registered_auxiliary_case_count": 73,
    }
    executable = [
        row
        for row in receipt["known_regression_inventory"]
        if row["machine_execution_required"]
    ]
    assert [(row["regression_id"], row["registered_case_count"]) for row in executable] == [
        ("V1_KNOWN_COMPARISON_28", 28),
        ("V2_DEVELOPMENT_42", 42),
    ]
    assert {row["required_receipt_role"] for row in executable} == {
        "known_regression_execution_receipt",
        "development_regression_execution_receipt",
    }


def test_s11_available_real_user_zero_requires_both_step1_and_step2() -> None:
    parents = _parents()
    receipt = build_available_input_scope_receipt(**parents)
    attestation = receipt["available_real_user_attestation"]
    assert attestation == {
        "collection_id": "real_user_current_valid",
        "classification": "real_user_current_valid",
        "registry_status": "not_received",
        "step1_intake_status": "not_received_not_blocking",
        "available_case_count": 0,
        "app_reachable_valid_count": 0,
        "execution_disposition": "zero_available_no_execution_fabricated",
        "storage": "private_local_only",
        "raw_body_included": False,
        "attestation_status": "frozen_zero_not_received",
    }

    mutated = deepcopy(parents)
    registry = mutated["step2_corpus_registry"]
    real_user = next(
        row
        for row in registry["collections"]
        if row["classification"] == "real_user_current_valid"
    )
    real_user["case_count"] = 1
    with pytest.raises(ValueError, match="step2_registry_parent_mismatch"):
        build_available_input_scope_receipt(**mutated)

    mutated = deepcopy(parents)
    mutated["step1_input_contract"]["supabase_future_intake"][
        "current_status"
    ] = "received"
    with pytest.raises(ValueError, match="step1_input_contract_parent_mismatch"):
        build_available_input_scope_receipt(**mutated)


def test_s11_every_registered_legacy_fixture_has_exact_disposition() -> None:
    parents = _parents()
    receipt = build_available_input_scope_receipt(**parents)
    rows = receipt["legacy_compatibility_inventory"]

    assert receipt["legacy_collection_binding"][
        "all_registered_cases_have_explicit_disposition"
    ] is True
    assert {row["fixture_id"] for row in rows} == {
        "legacy_backend_string_emotion",
        "legacy_self_insight_mixed",
        "legacy_string_emotion_array",
    }
    assert all(row["execution_disposition"] == "expected_non_applicable" for row in rows)
    assert {
        row["fixture_id"]: row["exact_validator_issue_codes"] for row in rows
    } == {
        "legacy_backend_string_emotion": ["input:keyset_mismatch"],
        "legacy_self_insight_mixed": [
            "input.emotions:self_insight_must_be_exclusive"
        ],
        "legacy_string_emotion_array": [
            "input.emotions[0]:keyset_mismatch"
        ],
    }

    for mutation in (
        lambda value: value["legacy_compatibility_inventory"].pop(),
        lambda value: value["legacy_compatibility_inventory"][0].update(
            {"exact_validator_issue_codes": ["input:invented"]}
        ),
        lambda value: value["legacy_compatibility_inventory"][0].update(
            {"execution_disposition": "app_reachable_to_execute"}
        ),
    ):
        forged = deepcopy(receipt)
        mutation(forged)
        assert validate_available_input_scope_receipt(
            forged, **parents
        ) == ("step11_available_input_scope_recomputed_value_mismatch",)


def test_s11_scope_source_hash_or_known_scope_cannot_false_green() -> None:
    parents = _parents()
    receipt = build_available_input_scope_receipt(**parents)
    mutations = (
        lambda value: value["source_registry_bindings"][2].update(
            {"sha256": "0" * 64}
        ),
        lambda value: next(
            row
            for row in value["known_regression_inventory"]
            if row["machine_execution_required"]
        ).update({"machine_execution_required": False}),
        lambda value: value["scope_aggregate"].update(
            {"known_machine_execution_case_count": 28}
        ),
        lambda value: value["available_real_user_attestation"].update(
            {"available_case_count": 1}
        ),
    )
    for mutation in mutations:
        forged = deepcopy(receipt)
        mutation(forged)
        assert validate_available_input_scope_receipt(
            forged, **parents
        ) == ("step11_available_input_scope_recomputed_value_mismatch",)
